# Project Repository Guide

Welcome to our project's repository! This README provides all the necessary information to get started with cloning the repository, setting up your development environment, collaborating with teammates, and running the project code.

## Cloning the Repository

To clone the repository and start working on the project, follow the instructions provided by GitHub at [GitHub Docs on Cloning a Repository](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

For additional Git guides and best practices, refer to [Git Guides](https://github.com/git-guides).

## Collaboration Workflow

### Moving to the Main Branch

To switch to the main branch:

```bash
git checkout main
```

### Rebasing

To rebase and update your local repository:

```bash
git pull --rebase
```

### Working on Feature Branches

To work on a feature branch:

```bash
git checkout my-feature-branch
```

### Committing Changes

After implementing your feature, commit changes by only adding Python files (do not add `__pycache__` or similar):

```bash
git add *.py
git commit -m "your message"
git push origin my-feature-branch
```

### Rebasing onto Main

Before merging, rebase your branch onto main:

```bash
git rebase main
```

### Submitting Pull Requests

After rebasing, submit a pull request through the GitHub web interface. Wait for your peers to review your changes and merge them into the main branch.

## Running the Code

### Prerequisites

Ensure Python is installed on your machine. To install Python, visit [Python Downloads](https://www.python.org/downloads/).

### Setting Up the Environment

1. Navigate to the root project directory.
2. Activate the virtual environment:

   - On macOS:
     ```bash
     source scrapyenv/bin/activate
     ```
   - On Windows:
     ```bash
     scrapyenv\Scripts\activate
     ```

### Running the Project

Within the virtual environment, navigate to the `rrid_project` directory and start the crawler:

```bash
cd rrid_project
scrapy crawl arxiv
# or
scrapy crawl biorxiv
```

### Installing Missing Packages

If you encounter missing packages, install them using pip:

```bash
pip install package_name
```

Happy coding! 🚀