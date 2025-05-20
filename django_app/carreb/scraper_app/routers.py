class ExternalDBRouter:
    def db_for_read(self, model, **hints):
        if hasattr(model, '_use_external'):
            return 'scraper_db'
        return None

    def db_for_write(self, model, **hints):
        if hasattr(model, '_use_external'):
            return 'scraper_db'
        return None
