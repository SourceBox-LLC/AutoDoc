# Project CADIA - CAD Generator Documentation

## Overview
Project CADIA is a web application designed to generate CAD files from natural language descriptions using the Zoo text-to-CAD API. Built with Streamlit, it provides a user-friendly interface for users to create and download CAD models effortlessly.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Installation](#installation)
3. [Application Structure](#application-structure)
4. [Using the CAD Generator](#using-the-cad-generator)
   - [Generating a CAD Model](#generating-a-cad-model)
   - [Handling Errors](#handling-errors)
5. [Customization](#customization)
6. [Best Practices](#best-practices)
7. [Common Issues and Solutions](#common-issues-and-solutions)

## Getting Started
To use Project CADIA, you will need to have Python installed, along with the necessary dependencies as specified in the `requirements.txt` file.

## Installation
1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Set Up a Virtual Environment (Optional but Recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Streamlit Secrets**
   Create a file named `secrets.toml` in the `.streamlit` directory and add your Zoo API key:
   ```toml
   [global]
   ZOO_API_KEY = "<your_api_key>"
   ```

## Application Structure
The application consists of the following main files:
- **app.py**: The main entry point for the Streamlit application.
- **cad.py**: Contains the logic to interact with the Zoo API and generate CAD files from text prompts.
- **requirements.txt**: Lists all the required Python packages.

## Using the CAD Generator

### Generating a CAD Model
To generate a CAD model, follow these steps:

1. **Run the Application**
   Start the Streamlit application with the following command:
   ```bash
   streamlit run app.py
   ```

2. **Access the Application**
   Open your web browser and navigate to `http://localhost:8501`.

3. **Input a Design Prompt