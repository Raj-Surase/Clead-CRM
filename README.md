# Clead CRM

Clead CRM is an open-source Customer Relationship Management (CRM) system designed to streamline lead management, calendar scheduling, and outreach automation. Built with a modern tech stack, it supports contributions from developers worldwide, including vibe coding enthusiasts. Licensed under the MIT License, Clead CRM is free to use, modify, and distribute.

## Features

- **Lead Management**: Import, track, and manage leads efficiently with file upload support.
- **Calendar Integration**: Schedule and manage appointments seamlessly.
- **Outreach Automation**: Automate email and messaging outreach for efficient communication.
- **Authentication**: Secure user authentication for safe access.
- **Open Source**: Welcomes contributions from the community under the MIT License.

## Project Structure

```
Clead-CRM/
├── backend/
│   ├── auth_backend/
│   ├── calendar_backend/
│   ├── config/
│   │   └── settings/
│   ├── lead_backend/
│   ├── outreach_backend/
│   ├── uploads/
│   ├── main.py
│   ├── requirements.txt
├── database/
│   ├── auth_db.sql
│   ├── calendar_db.sql
│   ├── form_submissions_db.sql
│   ├── lead_parser_db.sql
│   ├── outreach_db.sql
├── frontend/
│   ├── src/
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── README.md
├── README.md
└── LICENSE
```

## Tech Stack

- **Backend**: Python, FastAPI
- **Database**: MySQL
- **Frontend**: React, Vite, Tailwind CSS, Shadcn UI
- **License**: MIT

## Screenshots

![Dashboard](.assets/dashboard.webp)
*Main dashboard showing leads and calendar overview*

![Platforms Management](.assets/platforms.webp)
*Platforms management interface with multiple platform functionality*

![Calendar Management](.assets/calendar.webp)
*Calendar management interface for managing events*

*Note: Screenshots are placeholders. Contributors are welcome to add real screenshots to the `.assets/` directory.*

<!-- ## Demo

A short demo video showcasing Clead CRM's features is available [here](https://youtu.be/aNi5zIYMrz4).

<iframe width="560" height="315" src="https://www.youtube.com/embed/aNi5zIYMrz4" 
frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
allowfullscreen></iframe>


*Note: The demo video link is a placeholder. Contributors can record and upload a demo to the repository.* -->

## Getting Started

### Prerequisites

Ensure you have the following tools installed:

- **Windows, macOS, Linux**:
  - Python 3.9+
  - Node.js 18+
  - MySQL 8.0+
  - Git
  - pip (Python package manager)
  - npm or yarn (Node.js package manager)

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/Raj-Surase/clead-crm.git
   cd clead-crm
   ```

2. **Backend Setup**

   - Navigate to the backend directory:
     ```bash
     cd backend
     ```

   - Create a virtual environment:
     ```bash
     python -m venv venv
     source venv/bin/activate  # Linux/macOS
     venv\Scripts\activate     # Windows
     ```

   - Install dependencies:
     ```bash
     pip install -r requirements.txt
     ```

   - Set up environment variables:
     Create a `.env` file in the `backend/config/settings/` directory with the following:
     ```
     DATABASE_URL=mysql://username:password@localhost:3306/clead_crm
     SECRET_KEY=your-secret-key
     ```

   - Initialize the database:
     ```bash
     mysql -u username -p clead_crm < ../database/auth_db.sql
     mysql -u username -p clead_crm < ../database/calendar_db.sql
     mysql -u username -p clead_crm < ../database/form_submissions_db.sql
     mysql -u username -p clead_crm < ../database/lead_parser_db.sql
     mysql -u username -p clead_crm < ../database/outreach_db.sql
     ```

   - Run the backend server:
     ```bash
     uvicorn main:app --reload
     ```

3. **Frontend Setup**

   - Navigate to the frontend directory:
     ```bash
     cd frontend
     ```

   - Install dependencies:
     ```bash
     npm install
     # or
     yarn install
     ```

   - Start the development server:
     ```bash
     npm run dev
     # or
     yarn dev
     ```

4. **Database Setup**

   - Ensure MySQL is running.
   - Create a database named `clead_crm`:
     ```bash
     mysql -u username -p -e "CREATE DATABASE clead_crm;"
     ```

   - Apply the SQL scripts as shown in the backend setup.

### Platform-Specific Notes

- **Windows**:
  - Use Git Bash or WSL for Unix-like commands.
  - Ensure MySQL is added to your PATH.
  - Install MySQL: Download from [MySQL Community Server](https://dev.mysql.com/downloads/mysql/).

- **macOS**:
  - Install MySQL via Homebrew: `brew install mysql`.
  - Start MySQL: `brew services start mysql`.

- **Linux**:
  - Install MySQL: `sudo apt-get install mysql-server` (Ubuntu/Debian).
  - Start MySQL: `sudo service mysql start`.

## Contributing

We welcome contributions from everyone, including vibe coding enthusiasts! To contribute:

1. Fork the repository.
2. Create a new branch: `git checkout -b feature/your-feature`.
3. Make your changes and commit: `git commit -m "Add your feature"`.
4. Push to your branch: `git push origin feature/your-feature`.
5. Open a pull request.

<!-- Please follow the [Code of Conduct](CODE_OF_CONDUCT.md) and include tests for new features. -->

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Contact

For questions or feedback, open an issue or reach out on [LinkedIn](https://www.linkedin.com/in/raj-surase/) or send an email at rajsurase3@gmail.com.