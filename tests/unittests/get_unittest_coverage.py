import coverage
import unittest
import xmlrunner
from pathlib import Path
import os
import tarfile
import argparse
import json


run_examples = False

covered_classes = [
    "emodpy_typhoid.interventions.typhoid_vaccine"
    "emodpy_typhoid.interventions.outbreak",
    "emodpy_typhoid.interventions.tcc",
    "emodpy_typhoid.interventions.tcd",
    "emodpy_typhoid.interventions.typhoid.wash",
    "emodpy_typhoid.demographics.typhoid.TyphoidDemographics",
    "emodpy_typhoid.utility.sweeping"
]

class Coverage:
    def __init__(self):
        """
        Initialize to not replace existing results
        """
        self.set_baseline = False
        self.cov = None
        pass

    def get_baseline_bool(self):
        """
        Sets user input for saving coverage results json
        """
        parser = argparse.ArgumentParser(description="Settings for coverage logging")
        parser.add_argument(
            "--set_baseline",
            action="store_true",
            default=False,
            help="Use this flag to save the current coverage json as the baseline in coverage_data/.",
        )

        self.set_baseline = parser.parse_args().set_baseline

        pass

    def run_tests(self):
        self.cov = coverage.Coverage(source=covered_classes)
        self.cov.start()

        # First, load and run the unittest tests
        loader = unittest.TestLoader()
        test_suite = unittest.TestSuite()
        for folder in loader.discover(start_dir='.', pattern='test_*.py', top_level_dir=None):
            test_suite.addTest(folder)
        runner = xmlrunner.XMLTestRunner(output='test_reports')
        results = runner.run(test_suite)

        return results

    def save_results(self):
        """
        Saves new results and optionally baseline results,
        and print coverage by module
        """
        coverage_data = self.cov.get_data()
        measured_files = coverage_data.measured_files()

        # Getting the percentage coverage from the Coverage object
        def count_lines_in_file(file_path):
            try:
                with open(file_path, "r", encoding='utf-8') as file:
                    line = sum([1 for line in file])
                return line
            except FileNotFoundError:
                print(f"File not found: {file_path}")
                return None

        total_statements = 0
        total_covered_statements = 0
        coverage_results = {}
        for filename in measured_files:
            num_statements = count_lines_in_file(filename)
            covered_statements = len(coverage_data.lines(filename))

            total_statements += num_statements
            total_covered_statements += covered_statements

            coverage_percentage = round((covered_statements / num_statements) * 100, 2)
            coverage_results[filename] = coverage_percentage

        total_coverage_percentage = round((total_covered_statements / total_statements) * 100, 2)
        coverage_results["total_coverage"] = total_coverage_percentage

        # Formatting results to print out
        # Saving new results to /coverage_data
        new_results_path = Path.cwd() / 'coverage_data' / 'new_results.json'
        old_results_path = Path.cwd() / 'coverage_data' / 'baseline_results.json'
        os.makedirs(os.path.dirname(new_results_path), exist_ok=True)
        with open(new_results_path, "w", encoding='utf-8') as outfile:
            json.dump(coverage_results, outfile)

        if not os.path.exists(old_results_path):
            with open(old_results_path, "w", encoding='utf-8') as outfile:
                json.dump(coverage_results, outfile)

        # Access baseline results
        with open(old_results_path, "r", encoding='utf-8') as file:
            old_coverage_results = json.load(file)

        self.cov.save()
        self.cov.html_report()

        # Packaging as.tar.gz for jenkins
        print("Saving coverage file as: coverage.tar.gz")
        with tarfile.open("coverage.tar.gz", "w:gz") as tar:
            tar.add("htmlcov", arcname="coverage_app")  # Within coverage.tar.gz is coverage_app/files

    def run(self):
        self.get_baseline_bool()
        self.run_tests()
        self.cov.stop()
        self.save_results()


if __name__ == "__main__":
    coverage_class = Coverage()
    coverage_class.run()