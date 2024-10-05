import json
import os
import argparse
from datetime import datetime
from collections import defaultdict
import re
import hashlib
import sys

def sanitize_filename(filename):
    """Sanitize the filename to remove invalid characters."""
    if filename is None or filename.strip() == "":
        return "noname"
    invalid_characters = '<>:"/\\|?*\n\t'
    for char in invalid_characters:
        filename = filename.replace(char, '')
    return filename

def generate_hash(text):
    """Generate a short hash of the given text."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()[:6]

def get_conversation_text(node_id, mapping, conversation_text_list):
    """Extract the conversation text without formatting for keyword analysis."""
    node = mapping.get(node_id, {})
    if node.get('message') and 'content' in node['message'] and 'parts' in node['message']['content']:
        content_parts = node['message']['content']['parts']
        for part in content_parts:
            if isinstance(part, str):
                conversation_text_list.append(part)
            elif isinstance(part, dict) and 'text' in part:
                conversation_text_list.append(part['text'])
    for child_id in node.get('children', []):
        get_conversation_text(child_id, mapping, conversation_text_list)

def get_conversation(node_id, mapping, conversation_list, message_count):
    """Extract the conversation content with formatting for output."""
    node = mapping.get(node_id, {})
    if node.get('message') and 'content' in node['message'] and 'parts' in node['message']['content']:
        content_parts = node['message']['content']['parts']
        parts_text = []
        for part in content_parts:
            if isinstance(part, str):
                parts_text.append(part)
            elif isinstance(part, dict) and 'text' in part:
                parts_text.append(part['text'])
        if parts_text:
            author_role = node['message']['author']['role']
            if author_role == "user":
                conversation_list.append(f"<span style='color:#57130a;'>Human:</span>\n{''.join(parts_text)}\n")
            elif author_role == "assistant":
                conversation_list.append(f"<span style='color:#0a571f;'>ChatGPT:</span>\n{''.join(parts_text)}\n")
            elif author_role == "tool":
                tool_name = node['message']['author'].get('name', 'Unknown Tool')
                conversation_list.append(f"**{tool_name}:** {''.join(parts_text)}\n")
            message_count[0] += 1  # Increment message count
    for child_id in node.get('children', []):
        get_conversation(child_id, mapping, conversation_list, message_count)

def generate_unique_filename(base_path, title, datetime_iso):
    """Generate a unique filename with datetime."""
    filename = f"{datetime_iso}_{sanitize_filename(title)}"
    file_path = os.path.join(base_path, f"{filename}.md")
    return file_path

def create_index(output_dir, categorized_conversations):
    """Create an index file grouped by categories with date, time, and message count."""
    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, 'w', encoding='utf-8') as index_file:
        index_file.write("# Conversation Index\n\n")
        index_file.write("## Legend\n")
        index_file.write("🤖 Created | 🔄 Updated\n\n")
        for category, conversations in categorized_conversations.items():
            index_file.write(f"## {category}\n\n")
            index_file.write("| Status | Title | Created | Updated | Messages |\n")
            index_file.write("| :---: | :--- | :---: | :---: | :---: |\n")
            for convo in conversations:
                relative_path = os.path.relpath(convo['file_path'], output_dir).replace('\\', '/')
                # Escape pipe character in the link
                title_link = f"[[{relative_path}\\|{convo['title']}]]"
                index_file.write(f"| 🤖 | {title_link} | {convo['created']} | {convo['updated']} | {convo['messages']} |\n")
            index_file.write("\n")

def categorize_by_keywords_in_text(conversation_text, keywords_mapping):
    """Categorize a conversation based on keyword frequency in its text."""
    category_scores = {}
    for category, keywords in keywords_mapping.items():
        score = 0
        for keyword in keywords:
            # Count the occurrences of the keyword in the text
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', conversation_text, re.IGNORECASE))
            score += count
        if score > 0:
            category_scores[category] = score
    if category_scores:
        # Return the category with the highest score
        max_score = max(category_scores.values())
        # Find all categories with the max score (in case of tie)
        top_categories = [cat for cat, score in category_scores.items() if score == max_score]
        # You can choose to handle ties differently; here we select the first one
        return top_categories[0]
    else:
        return None

def generate_chatgpt_prompt(conversation_list):
    """Generate a prompt to simulate the conversation in ChatGPT."""
    prompt = ""
    for entry in conversation_list:
        if "<span style='color:#57130a;'>Human:</span>" in entry:
            content = entry.replace("<span style='color:#57130a;'>Human:</span>\n", "")
            prompt += f"Human: {content.strip()}\n"
        elif "<span style='color:#0a571f;'>ChatGPT:</span>" in entry:
            content = entry.replace("<span style='color:#0a571f;'>ChatGPT:</span>\n", "")
            prompt += f"ChatGPT: {content.strip()}\n"
        else:
            prompt += f"{entry.strip()}\n"
    return prompt.strip()

def generate_title_files(titles, output_dir, titles_per_file, prompt_text):
    """Generate .txt files with titles and ChatGPT prompt."""
    total_titles = len(titles)
    num_files = (total_titles + titles_per_file - 1) // titles_per_file  # Ceiling division

    for i in range(num_files):
        start_index = i * titles_per_file
        end_index = min(start_index + titles_per_file, total_titles)
        titles_chunk = titles[start_index:end_index]

        file_content = prompt_text + "\n\n"
        for title in titles_chunk:
            file_content += f"{title}\n"

        file_name = f"titles_part_{i+1}.txt"
        file_path = os.path.join(output_dir, file_name)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(file_content)
        print(f"Generated title file: {file_path}")

def load_categories_from_json(categories_json_files):
    """Load title-category mappings from JSON files."""
    categories_mapping = {}
    for file in categories_json_files:
        if not os.path.isfile(file):
            print(f"Warning: Categories JSON file '{file}' does not exist. Skipping.")
            continue
        with open(file, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    print(f"Warning: Categories JSON file '{file}' does not contain a dictionary. Skipping.")
                    continue
                for title, category in data.items():
                    sanitized_title = sanitize_filename(title)
                    categories_mapping[sanitized_title] = category.strip()
                print(f"Loaded categories from '{file}'.")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from file '{file}': {e}")
    return categories_mapping

def main():
    """Main function to process the conversations."""
    parser = argparse.ArgumentParser(description='Organize ChatGPT conversations into Obsidian-compatible Markdown files.')

    # Positional arguments
    parser.add_argument('input_files', nargs='+', help='JSON files containing conversations')
    parser.add_argument('output_dir', help='Directory to save output Markdown files')

    # Grouping and categorization options
    parser.add_argument('--group-by-time', action='store_true', help='Group conversations based on timestamp')
    parser.add_argument('--time-threshold', type=int, default=60, help='Time threshold in minutes for grouping conversations')
    parser.add_argument('--categorize-by-title', action='store_true', help='Categorize conversations based on titles')
    parser.add_argument('--categories_file', nargs='*', help='JSON files mapping titles to categories')
    parser.add_argument('--categorize-by-keywords', action='store_true', help='Categorize conversations based on keywords in message content')

    # New option for generating titles .txt files
    parser.add_argument('--split-titles', type=int, help='Number of titles per .txt file for ChatGPT prompts')

    # Other options
    parser.add_argument('--unprocessed-file', default='unprocessed.txt', help='File to save unprocessed titles')

    # Test mode (can be implemented as needed)
    parser.add_argument('--test', action='store_true', help='Enable test mode')

    args = parser.parse_args()

    # Check if output_dir exists, create if not
    if not os.path.isdir(args.output_dir):
        os.makedirs(args.output_dir)
        print(f"Created output directory: {args.output_dir}")

    data = []
    for input_file in args.input_files:
        if not os.path.isfile(input_file):
            print(f"Error: Input file '{input_file}' does not exist.")
            sys.exit(1)
        with open(input_file, 'r', encoding='utf-8') as f:
            try:
                data.extend(json.load(f))
                print(f"Loaded conversations from: {input_file}")
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from file '{input_file}': {e}")
                sys.exit(1)

    # Load categories mapping from JSON files if provided
    categories_mapping = {}
    if args.categories_file:
        categories_mapping = load_categories_from_json(args.categories_file)

    # Integrated keywords mapping
    keywords_mapping = {
    'DevOps': ['devops', 'ci/cd', 'jenkins', 'kubernetes', 'docker', 'ansible', 'terraform', 'prometheus', 'grafana', 'gitlab', 'circleci', 'chef', 'puppet'],
    'System Administration': ['mikrotik', 'nginx', 'ubuntu', 'server', 'zimbra', 'linux', 'windows server', 'active directory', 'dns', 'dhcp', 'apache', 'ftp', 'firewall', 'ssl', 'let\'s encrypt'],
    'Development/Programming': ['python', 'bash', 'powershell', 'git', 'script', 'javascript', 'js', 'html', 'css', 'c#', 'java', 'ruby', 'php', 'go', 'rust', 'typescript', 'node.js', 'django', 'flask'],
    'Web Development': ['html', 'css', 'javascript', 'js', 'react', 'angular', 'vue', 'node.js', 'express', 'wordpress', 'drupal', 'joomla', 'sass', 'bootstrap', 'tailwind', 'npm', 'webpack'],
    'Database Management': ['sql', 'mysql', 'postgresql', 'mongodb', 'database', 'oracle', 'sql server', 'nosql', 'redis', 'cassandra', 'sqlite', 'dbms', 'schema', 'replication', 'sharding'],
    'Networking': ['tcp', 'udp', 'vpn', 'firewall', 'routing', 'switching', 'cisco', 'network', 'ip', 'subnet', 'dhcp', 'lan', 'wan', 'bgp', 'ospf', 'icmp', 'nat', 'dhcp'],
    'Cloud Computing': ['aws', 'azure', 'gcp', 'cloud', 'ec2', 's3', 'lambda', 'cloudformation', 'cloudwatch', 'docker', 'kubernetes', 'serverless', 'rds', 'load balancer', 'autoscaling', 'iam', 'terraform'],
    'Security': ['rsa', 'aes', 'sha', 'encryption', 'cybersecurity', 'ssl', 'tls', 'firewall', 'vulnerability', 'penetration testing', 'hacking', 'malware', 'ransomware', 'phishing', 'ddos', 'brute force', 'zero-day', 'backdoor', 'keylogger', 'siem', 'ids', 'ips', 'soc', 'threat hunting'],
    'Artificial Intelligence': ['ai', 'machine learning', 'deep learning', 'neural network', 'tensorflow', 'pytorch', 'nlp', 'computer vision', 'reinforcement learning', 'supervised learning', 'unsupervised learning', 'gpt', 'transformer', 'classification', 'regression', 'clustering', 'cnn', 'rnn'],
    'Data Science': ['data science', 'data analysis', 'pandas', 'numpy', 'matplotlib', 'statistics', 'data visualization', 'regression', 'classification', 'clustering', 'big data', 'hadoop', 'spark', 'etl', 'data pipeline', 'data wrangling', 'jupyter', 'sql', 'excel'],
    'Project Management': ['agile', 'scrum', 'kanban', 'project management', 'jira', 'confluence', 'trello', 'waterfall', 'pmp', 'scope', 'risk management', 'stakeholder', 'milestones', 'deliverables'],
    'Personal Development': ['productivity', 'time management', 'self-improvement', 'career', 'motivation', 'leadership', 'communication', 'teamwork', 'emotional intelligence', 'problem solving', 'decision making'],
    'Health and Wellness': ['health', 'fitness', 'nutrition', 'mental health', 'wellness', 'exercise', 'diet', 'vitamin', 'therapy', 'meditation', 'yoga', 'supplements', 'hydration', 'stress management'],
    'Travel': ['visa', 'travel', 'passport', 'immigration', 'flight', 'hotel', 'tourism', 'itinerary', 'booking', 'customs', 'airport', 'baggage', 'trip', 'insurance', 'reagrupación familiar', 'permiso de trabajo', 'obtención ciudadanía'],
    'Language Learning': ['english', 'spanish', 'russian', 'language', 'learning', 'grammar', 'vocabulary', 'ielts', 'toefl', 'esl', 'speaking', 'listening', 'writing', 'reading'],
    'Hardware': ['raspberry pi', 'arduino', 'hardware', 'cpu', 'gpu', 'motherboard', 'ssd', 'hdd', 'ram', 'power supply', 'peripherals', 'usb', 'bios', 'overclocking', 'cooling', 'raspbian', 'firmware', 'pixel 8 pro', 'móviles'],
    'E-Commerce': ['promo code', 'discount', 'free shipping', 'return policy', 'coupon', 'checkout', 'gift card', 'deal', 'sale'],
    'Support and Troubleshooting': ['help desk', 'it support', 'troubleshoot', 'ticketing', 'incident management', 'escalation', 'remote support', 'system logs', 'error logs', 'patching', 'backup', 'restore', 'diagnostics', 'sla', 'downtime', 'uptime', 'root cause analysis', 'Touch Screen Confirmation'],
    'Finance and Investment': ['dividends', 'capped amount', 'investment return', 'passive income', 'ganar €20,000', '€', '$', '£', '¥'],
    'Entertainment': ['series de fantasía', 'películas', 'libros de fantasía', 'videojuegos', 'música', 'arte digital', 'streaming', 'comics', 'novelas gráficas'],
    'Legal and Documentation': ['legal document', 'contract', 'agreement', 'terms and conditions', 'privacy policy', 'license', 'certification', 'visa application', 'residence permit', 'tax id', 'work permit', 'official document', 'notarized document', 'birth certificate'],
    'Miscellaneous': []
    }

    # Warn if categorize-by-keywords is enabled but keywords_mapping is empty
    if args.categorize_by_keywords and not keywords_mapping:
        print("Warning: 'categorize-by-keywords' is enabled but 'keywords_mapping' is empty. Please populate 'keywords_mapping' with appropriate keywords.")

    categorized_conversations = defaultdict(list)
    unprocessed_titles = []
    all_titles = []  # To collect all titles for generating title files

    for item in data:
        title = item.get("title")
        if not title:
            continue  # Skip if no title
        title_sanitized = sanitize_filename(title)
        all_titles.append(title_sanitized)
        category = None

        # Assign category from categories_file if available
        if title_sanitized in categories_mapping:
            category = categories_mapping[title_sanitized]
        else:
            # First, try categorizing by content keywords
            if args.categorize_by_keywords:
                conversation_text_list = []
                root_node_id = next((node_id for node_id, node in item['mapping'].items() if node.get('parent') is None), None)
                if root_node_id:
                    get_conversation_text(root_node_id, item['mapping'], conversation_text_list)
                    conversation_text = ' '.join(conversation_text_list)
                    category = categorize_by_keywords_in_text(conversation_text, keywords_mapping)

            # If categorization by content keywords fails, try categorizing by title keywords
            if not category and args.categorize_by_title:
                # Try to categorize based on title keywords
                category = categorize_by_keywords_in_text(title_sanitized, keywords_mapping)

            # If still no category, assign 'Unprocessed'
            if not category:
                category = 'Unprocessed'
                unprocessed_titles.append(title_sanitized)

        # Generate date and hash for folder name
        create_time = item.get("create_time")
        if not create_time:
            print(f"Warning: 'create_time' not found for conversation '{title}'. Using current time.")
            datetime_obj = datetime.now()
        else:
            datetime_obj = datetime.fromtimestamp(create_time)
        date_str = datetime_obj.strftime('%Y-%m-%d')
        hash_str = generate_hash(title_sanitized + str(create_time))
        folder_name = f"{date_str}-{hash_str}"

        # Create category folder within output_dir
        category_folder = os.path.join(args.output_dir, category)
        if not os.path.isdir(category_folder):
            os.makedirs(category_folder)
            print(f"Created category folder: {category_folder}")

        # Create conversation folder within category
        conversation_folder = os.path.join(category_folder, folder_name)
        if not os.path.isdir(conversation_folder):
            os.makedirs(conversation_folder)
            print(f"Created conversation folder: {conversation_folder}")

        # Extract conversation content for output
        conversation_output = []
        message_count = [0]  # Initialize message count
        root_node_id = next((node_id for node_id, node in item['mapping'].items() if node.get('parent') is None), None)
        if root_node_id is None:
            print(f"Error: Could not find root node for conversation '{title}'")
            continue
        get_conversation(root_node_id, item['mapping'], conversation_output, message_count)

        # Generate filename with datetime
        datetime_iso = datetime_obj.strftime('%Y-%m-%d_%H-%M-%S')
        file_path = generate_unique_filename(conversation_folder, title_sanitized, datetime_iso)

        print(f"Writing conversation '{title}' to: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as outfile:
            outfile.write('\n'.join(conversation_output))

        # Generate ChatGPT prompt and save it
        prompt = generate_chatgpt_prompt(conversation_output)
        prompt_file_path = os.path.join(conversation_folder, f"{datetime_iso}_{sanitize_filename(title)}_prompt.txt")
        with open(prompt_file_path, 'w', encoding='utf-8') as prompt_file:
            prompt_file.write(prompt)
        print(f"Generated ChatGPT prompt file: {prompt_file_path}")

        # Get the file's last modified time
        try:
            updated_time = datetime.fromtimestamp(os.path.getmtime(file_path))
            updated_str = updated_time.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error getting modified time for '{file_path}': {e}")
            updated_str = "Unknown"

        # Add to categorized conversations for indexing
        datetime_str = datetime_obj.strftime('%Y-%m-%d %H:%M:%S')
        categorized_conversations[category].append({
            'title': title_sanitized,
            'created': datetime_str,
            'updated': updated_str,
            'messages': message_count[0],
            'file_path': file_path
        })

    # Create index file
    print("Creating index.md...")
    create_index(args.output_dir, categorized_conversations)
    print(f"Created index.md at: {os.path.join(args.output_dir, 'index.md')}")

    # Write unprocessed titles to file
    if unprocessed_titles:
        unprocessed_path = os.path.join(args.output_dir, args.unprocessed_file)
        with open(unprocessed_path, 'w', encoding='utf-8') as unprocessed_file:
            unprocessed_file.write('\n'.join(unprocessed_titles))
        print(f"Unprocessed titles saved in: {unprocessed_path}")

    # Generate .txt files with titles and ChatGPT prompt if --split-titles is specified
    if args.split_titles:
        # Define the ChatGPT prompt
        chatgpt_prompt = (
    "Please help categorize the following conversation titles into appropriate categories. "
    "For each title, assign a category that best describes its content. "
    "Provide the output in the format 'Title: Category'. "
    "Ensure that the output is structured as a JSON object.\n"
    "Example:\n"
    "{\n"
    "    'How to cook pasta': 'Cooking',\n"
    "    'Best practices in Python': 'Programming',\n"
    "    'Understanding financial markets': 'Finance'\n"
    "}\n"
    "Now, here are the titles:"
        )
        print("Generating title .txt files with ChatGPT prompts...")
        generate_title_files(all_titles, args.output_dir, args.split_titles, chatgpt_prompt)
        print("Title .txt files generation complete.")

    print("Processing complete.")

if __name__ == '__main__':
    main()


