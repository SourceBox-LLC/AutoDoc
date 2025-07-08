# Project CADIA - CAD Generator Documentation

Welcome to the documentation for **Project CADIA**, a powerful CAD (Computer-Aided Design) generator that allows users to create 3D models from textual descriptions. This project leverages advanced machine learning algorithms to translate natural language prompts into CAD files, making design more accessible and efficient for users across various industries.

## Overview

Project CADIA provides a user-friendly interface built with Streamlit, enabling users to describe their CAD designs in simple language and receive a 3D model in return. The application is equipped with a seamless integration to the Zoo text-to-CAD API, facilitating the conversion of prompts into CAD files, specifically in formats like STEP and STL.

## Table of Contents

- [Getting Started](#getting-started)
- [Components](#components)
  - [app.py](#apppy)
  - [cad.py](#cadpy)
- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

## Getting Started

To get started with Project CADIA, ensure you have Python installed along with the necessary dependencies listed in `requirements.txt`. You can set up the environment by following the installation instructions below.

## Components

### app.py

The main entry point for the Project CADIA application, responsible for the user interface and interaction. It utilizes Streamlit to create a web application that allows users to input their design prompts and view the generated CAD models.

### cad.py

Contains the core logic for generating CAD files using the Zoo text-to-CAD API. This module includes the `generate_cad` function, which takes user prompts and produces corresponding CAD files, managing API interactions and error handling throughout the process.

## Installation

To install the necessary dependencies for Project CADIA, run the following command in your terminal:

```bash
pip install -r requirements.txt
```

Make sure you also configure the API key in your Streamlit secrets file to enable access to the Zoo text-to-CAD API.

## Usage

After the setup is complete, you can run the application by executing the following command in your terminal:

```bash
streamlit run app.py
```

This will launch the web interface where you can start generating CAD files by describing your designs in natural language.

## Contributing

We welcome contributions to Project CADIA! Please fork the repository and submit a pull request for any enhancements, bug fixes, or improvements.

## License

This project is licensed under the MIT License