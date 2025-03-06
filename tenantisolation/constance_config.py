CONSTANCE_CONFIG = {
    "SITE_NAME": ("Test", ""),
    "STATIC_VERSION": ("1.0.0", "Static version"),
    "ADMIN_SITE_ISOLATION": (
        True,
        "Enable/Disable Tenant Isolation for the admin panel.",
    ),
    "SITE_DOMAIN": ("", "Site domain"),
    "SITE_COLOR": ("#2563eb", "Theme color of the site (in hexadecimal format)."),
}

CONSTANCE_CONFIG_FIELDSETS = {
    "GENERAL": [
        "SITE_NAME",
        "SITE_DOMAIN",
        "SITE_COLOR",
        "STATIC_VERSION",
        "ADMIN_SITE_ISOLATION",
    ],
}
