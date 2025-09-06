#!/bin/bash

# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Create the database tables
python create_db.py```

**Step 4: Create a GitHub Repository and Push Your Code**
1.  Go to [GitHub](https://github.com/) and create a new repository (e.g., `ai-fitness-app`).
2.  Follow the instructions on GitHub to "push an existing repository from the command line." It will look something like this (run these in your `ai_fitness_app` folder):
    ```bash
    git init -b main
    git add .
    git commit -m "Initial commit of AI Fitness App"
    git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
    git push -u origin main
    ```

**Step 5: Deploy on Render**
1.  Sign up or log in to [Render](https://dashboard.render.com/).
2.  **Create a PostgreSQL Database:**
    *   Go to "New" -> "PostgreSQL".
    *   Give it a name (e.g., `fitness-db`).
    *   Copy the "Internal Database URL". You will need it soon.
3.  **Create a Web Service:**
    *   Go to "New" -> "Web Service".
    *   Connect the GitHub repository you just created.
    *   Give your service a name (e.g., `ai-fitness-app`).
    *   **Root Directory:** Leave this blank.
    *   **Environment:** `Python 3`
    *   **Region:** Choose one close to you.
    *   **Build Command:** `./build.sh`
    *   **Start Command:** `gunicorn app:app`
4.  **Add Environment Variables:**
    *   Click on the "Environment" tab for your new web service.
    *   Click "Add Environment Variable".
        *   **Key:** `DATABASE_URL`
        *   **Value:** Paste the "Internal Database URL" you copied from your PostgreSQL database.
    *   Click "Add Environment Variable" again.
        *   **Key:** `PYTHON_VERSION`
        *   **Value:** `3.12.0` (or your local Python 3 version)
5.  **Deploy:**
    *   Click "Create Web Service".

Render will now pull your code from GitHub, install the dependencies, run your `build.sh` script to create the database tables, and start the Gunicorn server. You can watch the progress in the "Logs" tab. Once it says "Your service is live," you can click the URL at the top of the page.

Your AI Fitness application is now live on the internet. Congratulations