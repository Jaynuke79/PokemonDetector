# PokemonDetector

A web application that detects Pokémon from images.  
Originally built as a class project, this repository demonstrates modern project development and management practices.

---

## 🚀 Project Goals

- **Familiarize with project management tools**
- **Containerize with Docker**
- **Develop frontend with Replit**
- **Implement ML with PyTorch**

---

## 🗂️ Directory Structure

| Directory      | Purpose                        |
| -------------- | ----------------------------- |
| **app/**       | Web server & API code          |
| **data/**      | Datasets and related files     |
| **frontend/**  | Frontend (UI) source code      |
| **scripts/**   | Utility and helper scripts     |
| **tests/**     | Automated tests                |

---

## 📦 Deliverable

A web app that hosts a Pokémon detector.

---

## 📝 Project Management

- **UV** for project management
- **Docker** for containerization
- **Replit** for frontend development
- **PyTorch** for machine learning

---

## 🗒️ Walk Throughs

| Topic | Cmds | Note(s) |
|-------|------|---------|
| UV Env Terminal | `source .venv/bin/activate` | Opens Terminal in UV Env as defined in `.venv` <br> _Works as if you put `uv run` in front of all cmds_ |
| CLI Script: `poke` | `uv run poke <img_path>` | Predicts what Pokémon is in the image <br> _Requires downloading of [model](https://drive.google.com/file/d/1jbtCxdDw7YZHVrTwmaona2r9ScCpnXm-/view?usp=sharing) to `scirpts/cli`_ <br> _Default model is trained on Gen1 only_ |

---

Feel free to explore the directories and contribute!