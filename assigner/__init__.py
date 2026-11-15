from .load import load_photo
from .assign import assign
from .report import build_report


def process_file(path):
    photo = load_photo(path)
    return build_report(photo, assign(photo))
