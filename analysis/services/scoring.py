class ScorePalette:
    NEUTRAL = ""
    DANGER = "danger"
    WARN = "warn"
    ACCENT = "accent"

    DANGER_BELOW = 50
    WARN_BELOW = 75

    @classmethod
    def tone(cls, value):
        if value is None:
            return cls.NEUTRAL
        if value < cls.DANGER_BELOW:
            return cls.DANGER
        if value < cls.WARN_BELOW:
            return cls.WARN
        return cls.ACCENT
