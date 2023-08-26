import logging

from xmlrunner.extra.djangotestrunner import XMLTestRunner


class NoLoggingTestRunner(XMLTestRunner):
    """
    Generates XML file for gitla tests, and disables logging
    """

    def run_tests(self, test_labels, extra_tests=None, **kwargs):
        # Don't show logging messages while testing
        logging.disable(logging.CRITICAL)
        return super().run_tests(test_labels, extra_tests, **kwargs)
