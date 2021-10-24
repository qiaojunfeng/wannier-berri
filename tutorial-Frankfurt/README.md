This tutorial dials with the newest version, which is not even merged to the master branch yet 
(but will be merged soon) to be on a safe side, it is recommended to create a virtual 
environment. To do that:

1. Clone the repository to your local computer, `git clone ...`
2. Ensure you have a modern version of Python installed (3.6 or higher). 
3. Create a new development environment. Either use a virtual environment, for example:
   ```
   python -m venv /path/to/wberri_test_env
   ```
   or, if you're using [anaconda](), a new conda environment.
   ```
   conda create --name wberri_test_env
   ```
4. Activate this virtual environment or conda environment, e.g. by running 
   `source /path/to/wberri_test_env/bin/activate` or 
   `conda activate wberri_test_env` as appropriate.

5. Go into the repository directory and run `python setup.py install`.

Alternatively, in the directory where you run the tutoril, do `ln -s /path/to/wannierberri .`
and install all dependencies manually.
