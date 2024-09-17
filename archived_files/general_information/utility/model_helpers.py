import uuid
import os

# file will be uploaded to MEDIA_ROOT / uploads / app_name


def get_upload_image_path(instance, filename):
    ext = filename.split(".")[-1]
    name = "{}.{}".format(uuid.uuid4(), ext)
    return os.path.join("uploads/sport_information", name)


SPORT_CHOICES = (
    ("Mens Football", "Mens Football"),
    ("Coed Football", "Coed Football"),
    ("Other Football", "Other Football"),
    ("Mens Basketball", "Mens Basketball"),
    ("Womens Basketball", "Womens Basketball"),
    ("Coed Basketball", "Coed Basketball"),
    ("Other Basketball", "Other Basketball"),
    ("Mens Soccer", "Mens Soccer"),
    ("Womens Soccer", "Womens Soccer"),
    ("Coed Soccer", "Coed Soccer"),
    ("Other Soccer", "Other Soccer"),
)

SPORT_LEVEL = (
    ("High School", "High School"),
    ("College", "College"),
    ("Professional", "Professional"),
)