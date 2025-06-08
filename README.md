# Lightning MD - AI-Powered Documentation Generator

Lightning MD helps developers quickly generate comprehensive documentation for code repositories using AI.

## Features

- **Repository Integration**: Pull GitHub repositories and analyze their contents
- **AI Documentation Generation**: Generate comprehensive documentation with Lightning Sprint or Draft modes
- **Documentation Review and Saving**: Edit, review, and save the generated documentation
- **Step-by-Step Workflow**: Linear interface with locked steps to ensure proper workflow

## Deployment to Streamlit Community Cloud

To deploy this app to Streamlit Community Cloud:

1. **Push your code to GitHub**
   - Ensure `.streamlit/secrets.toml` is in your `.gitignore` file (already added)

2. **Sign up for Streamlit Community Cloud**
   - Visit [https://streamlit.io/cloud](https://streamlit.io/cloud) and sign in with GitHub

3. **Deploy the app**
   - Click "New app"
   - Select your repository, branch, and `app.py` as the main file
   - Click "Deploy!"

4. **Configure secrets**
   - In your deployed app settings, find the "Secrets" section
   - Add your secrets in TOML format:
   ```toml
   [openai]
   api_key = "your-actual-openai-api-key"
   ```

## Local Development

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Lightning-MD
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up secrets**
   - Create `.streamlit/secrets.toml` with your OpenAI API key:
   ```toml
   [openai]
   api_key = "your-openai-api-key"
   ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Project Structure

- `app.py`: Main Streamlit application
- `ai.py`: AI integration with OpenAI API
- `repo_tools.py`: GitHub repository management utilities
- `.streamlit/secrets.toml`: Configuration secrets (not committed to git)
- `requirements.txt`: Dependencies list

## License

[Your license information]
