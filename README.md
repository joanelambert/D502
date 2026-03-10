# D502 Project

A Python-based data science and analysis project.

## Project Structure

```
D502/
├── data/            # Raw and cleaned data
├── src/             # Source code modules
├── notebooks/       # Jupyter notebooks for exploration and analysis
├── tests/           # Unit tests
├── requirements.txt # Python package dependencies
├── README.md        # This file
└── .github/         # GitHub configuration and instructions
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Setup Steps

1. **Clone or navigate to the project directory:**
   ```bash
   cd D502
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**

   **On Windows:**
   ```bash
   venv\Scripts\activate
   ```

   **On macOS/Linux:**
   ```bash
   source venv/bin/activate
   ```

4. **Install required packages:**
   ```bash
   pip install -r requirements.txt
   ```

## Dependencies

The project uses the following main packages:

- **NumPy** - Numerical computing and array operations
- **Pandas** - Data manipulation and analysis
- **scikit-learn** - Machine learning algorithms
- **Jupyter** - Interactive notebook environment
- **Matplotlib** - Data visualization
- **Seaborn** - Statistical data visualization

## Usage

### Running Jupyter Notebooks

To start the Jupyter Lab environment:

```bash
jupyter lab
```

Then navigate to the `notebooks/` directory to create or open notebooks.

### Running Python Scripts

To run a Python script from the `src/` directory:

```bash
python -m src.your_module_name
```

## Project Guidelines

- Place reusable code in the `src/` directory
- Use `notebooks/` for exploratory analysis and prototyping
- Add unit tests to the `tests/` directory
- Keep the virtual environment activated when working on the project
- Update `requirements.txt` when adding new dependencies

## License

This project is part of an educational data science curriculum.
