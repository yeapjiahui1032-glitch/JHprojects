# Streamlit Cloud Deployment Guide

## 🚀 Deploying to Streamlit Cloud

### Prerequisites
1. A GitHub account
2. An OpenAI API key
3. Your code pushed to a GitHub repository

### Step-by-Step Deployment

#### 1. Prepare Your Repository
Ensure your repository has these files in the root directory:
- `app.py` (your main Streamlit app)
- `requirements.txt` (dependencies)
- `.streamlit/config.toml` (Streamlit configuration)
- `.streamlit/secrets.toml.example` (secrets template)

#### 2. Set Up Secrets in Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect your GitHub account
3. Select your repository and branch
4. In the app settings, go to "Secrets"
5. Add your OpenAI API key:
   ```
   OPENAI_API_KEY = "your-actual-openai-api-key-here"
   ```

#### 3. Deploy
1. Click "Deploy" in Streamlit Cloud
2. Wait for the build to complete
3. Your app will be live at a URL like: `https://your-app-name.streamlit.app`

### Troubleshooting

#### Build Failures
- Check the build logs in Streamlit Cloud
- Ensure all packages in `requirements.txt` are compatible
- Verify your Python code doesn't have syntax errors

#### Runtime Errors
- Check that your OpenAI API key is correctly set in secrets
- Ensure your app handles missing API keys gracefully
- Test locally first: `streamlit run app.py`

#### Common Issues
1. **"Module not found"**: Add missing packages to `requirements.txt`
2. **"OpenAI API key not found"**: Set the secret in Streamlit Cloud dashboard
3. **"Config option not supported"**: Remove incompatible options from `config.toml`

### File Structure
```
your-repo/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Python dependencies
├── .streamlit/
│   ├── config.toml          # Streamlit configuration
│   └── secrets.toml.example # Secrets template (don't commit actual secrets)
└── README.md                # Your project documentation
```

### Cost Considerations
- OpenAI API calls will incur costs based on usage
- Streamlit Cloud is free for public apps
- Monitor your OpenAI usage in their dashboard

### Security Notes
- Never commit API keys to your repository
- Use Streamlit secrets for sensitive configuration
- Keep your `secrets.toml.example` file for documentation