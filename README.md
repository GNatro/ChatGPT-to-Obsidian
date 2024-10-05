# **ChatGPT_to_Obsidian**



A Python script to convert your exported ChatGPT JSON conversations into organized Markdown files, compatible with Obsidian. This tool not only converts your conversations but also categorizes them based on keyword analysis and, with the help of AI, you can organize them even better for easier navigation and management.

Both **Content-Keyword-Based**, **Title-Keyword-Based**, and **Title-Manual-Based** categorization modes are supported.

------

​                                                                                                             [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/K3K814BTPJ)

------

## 📦 **Installation**

Clone the repository:

```bash
git clone https://github.com/GNatro/ChatGPT-to-Obsidian.git
```

Navigate to the directory:

```bash
cd ChatGPT_to_Obsidian
```

------

## 🚀 **Features**

- **Export to Markdown**: Converts ChatGPT JSON conversations into Markdown `.md` files.
- **Keyword-Based Categorization**: Organizes conversations into categories based on keyword frequency in content and titles.
- **AI Organized Categorization**: After organizing the titles into categories with AI, you can input the `.json` categorized file for better results (Recommended).
- **Structured Directory**: Creates a structured directory compatible with Obsidian for easy navigation.
- **Index Generation**: Generates an `index.md` file with links to all conversations, including metadata like creation date and message count.
- **Obsidian Compatibility**: Supports Obsidian features like hover previews and internal linking.

------

## 🔧 **Usage**

### **Command-Line Options**

```bash
usage: ChatGPT_to_Obsidian.py [-h] [--group-by-time] [--time-threshold TIME_THRESHOLD]
                              [--categorize-by-title]
                              [--categories_file [CATEGORIES_FILE ...]]
                              [--categorize-by-keywords]
                              [--unprocessed-file UNPROCESSED_FILE]
                              [--split-titles SPLIT_TITLES]
                              input_files [input_files ...] output_dir

Organize conversations into categories.

positional arguments:
  input_files           JSON files containing conversations
  output_dir            Directory to save output Markdown files

options:
  -h, --help            show this help message and exit
  --group-by-time       Group conversations based on timestamp
  --time-threshold TIME_THRESHOLD
                        Time threshold in minutes for grouping conversations
  --categorize-by-title Categorize conversations based on titles
  --categories_file [CATEGORIES_FILE ...]
                        JSON files mapping titles to categories
  --categorize-by-keywords
                        Categorize conversations based on keywords in message content
  --split-titles SPLIT_TITLES
                        Number of titles per .txt file for ChatGPT prompts
  --unprocessed-file UNPROCESSED_FILE
                        File to save unprocessed titles
```

------

## **Steps to Run the Script**

### **1. Export Your Conversations**

In your browser:

- Login to chat.openai.com
- Go to **Settings > Export Data** > Export to download your conversations as a JSON file.

------

### **2. Prepare Your Conversations**

- Place your exported ChatGPT conversation JSON file(s) in a folder.
- Example file: `conversations.json`

------

### **3. Split Titles for Categorization**

Before categorizing your conversations, you need to split the titles and prepare them for categorization.

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --split-titles 200
```

- This command will split your conversation titles into `.txt` files, with 200 titles per file.
- Each file will contain a prompt asking ChatGPT (or another tool) to categorize the titles into JSON format.

------

### **4. Categorize Your Conversations Using the JSON File**

Once you have categorized your titles using ChatGPT or any other tool, save the categorized titles into a `categories.json` file. **Make sure the file format is `.json`.**

Here is an example of how the `categories.json` structure should look:

```json
{
    "How to fix server issues": "System Administration",
    "Deploying with Jenkins": "DevOps",
    "Best cooking recipes": "Cooking",
    "Traveling to Japan": "Travel"
}
```

- **Title**: This is the exact title from the conversation JSON file.
- **Category**: This is the category you want to assign to the conversation.

Now, you can run the script with this JSON file to organize the conversations.

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --categories_file categories.json
```

------

### **Using All Categorization Options at Once**

You can combine **content-based**, **title-based**, and **manual categorization with the AI-generated JSON file** in one command to categorize your conversations comprehensively.

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --categorize-by-keywords --categorize-by-title --categories_file categories.json
```

#### **Explanation of the Process**:

When you use all options together (`--categorize-by-keywords`, `--categorize-by-title`, and `--categories_file`), the script follows this order:

1. **Title-Based Categorization**: The script first attempts to categorize conversations based on keywords found in the titles.
2. **Content-Based Categorization**: If the title does not match any keyword, the script scans the content of the conversation for predefined keywords and attempts to categorize it.
3. **Manual Categorization (AI-generated JSON)**: If the conversation could not be categorized by title or content, it uses the `categories.json` file you provided, which contains the manually organized categories (often AI-generated).

This ensures that your conversations are organized comprehensively using all available methods, and any missing categories can be resolved with the help of the AI-generated JSON file.

------

## **Examples**

### 🚀 **Example 1: Categorize by Content and Title Keywords**

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --categorize-by-keywords --categorize-by-title
```

### 🕒 **Example 2: Group Conversations by Time**

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --group-by-time --time-threshold 60
```

### 📁 **Example 3: Categorizing Conversations Using a JSON Categories File**

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --categories_file categories.json
```

### 🔗 **Example 4: Using All Categorization Methods Together**

```bash
python3 ChatGPT_to_Obsidian.py conversations.json output_directory --categorize-by-keywords --categorize-by-title --categories_file categories.json
```

------

## 📂 **Directory Structure**

- **Category Folders**: Conversations are grouped into categories based on keywords or title-based mappings.
- **Date-Hash Folders**: Each conversation is stored in a folder named with the date and a unique hash.
- **Markdown Files**: Conversations are saved as Markdown files with timestamps and sanitized titles.
- **Index File**: An `index.md` file at the root of the output directory links to all conversations.

### **Example Directory Structure**:

```bash
output_directory/
  Category/
    YYYY-MM-DD-abcdef/
      YYYY-MM-DD_HH-MM-SS_Title.md
  index.md
```

------

## 📝 **Index Example**

The `index.md` file is a table listing all conversations:

| Status | Title                                                     | Created              | Updated       | Messages      |
| ------ | --------------------------------------------------------- | -------------------- | ------------- | ------------- |
| 🤖      | [[Category/YYYY-MM-DD-abcdef/YYYY-MM-DD_HH-MM-SS_Title.md | Conversation Title]] | YYYY-MM-DD HH | YYYY-MM-DD HH |

- **Status**: An icon indicating the status (e.g., 🤖 for created).
- **Title**: A link to the conversation file.
- **Created**: The creation date and time.
- **Updated**: The last modification date and time.
- **Messages**: The number of messages in the conversation.

------

## ✨ **Features Explained**

### **Keyword-Based Categorization**

The script first tries to categorize conversations based on the frequency of keywords in the content. If that fails, it attempts categorization using keywords in the title.

### **Message Count**

Counts the number of messages in each conversation and includes this in the index.

### **Status Icons**

Uses icons to indicate the status of each conversation. You can customize these icons if desired.

### **Obsidian Hover Previews**

By leveraging Obsidian's features, hovering over a link in the index shows a preview of the conversation.

------

## 🔄 **Customization**

### **Adding or Modifying Keywords**

Customize the categories and keywords by modifying the `keywords_mapping` dictionary in the script:

```python
keywords_mapping = {
    'DevOps': ['devops', 'ci/cd', 'jenkins', 'kubernetes', 'docker'],
    'System Administration': ['mikrotik', 'nginx', 'ubuntu', 'server', 'linux'],
    # Add more categories and keywords as needed
}
```

------

## ⚡ **Rate Limits**

To handle large numbers of conversations:

- **Add Time Gaps**: If you're processing many files, consider adding delays between processing to manage system resources.
- **Batch Processing**: Split your conversations into batches and process them separately.

------

## 📋 **Notes**

- **Content Analysis**: Analyzes the internal content of the messages, not just the titles, for accurate categorization.
- **Dependencies**: No additional Python packages are required beyond the standard library.
- **Compatibility**: Compatible with Windows, macOS, and Linux.

------

## 📄 **License**

This project is licensed under the MIT License.

------

## 💖 **Support Me**

If you find this tool helpful and want to support its development, consider buying me a coffee:

​                                                                                                             [![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/K3K814BTPJ)

------

## 🙌 **Contributing**

Contributions are welcome! If you have suggestions or improvements, feel free to open an issue or submit a pull request.

------

## 👮 **Legal**

This is a third-party tool and is not associated with OpenAI or ChatGPT. It's strictly for personal and educational purposes. You are responsible for complying with OpenAI's terms of service and any applicable laws.

------

## 📞 **Contact**

For questions or additional support, you can contact the project maintainer:

- **Name**: George
- **Email**: info.georgen@gmail.com

