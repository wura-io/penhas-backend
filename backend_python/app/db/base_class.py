from sqlalchemy.orm import DeclarativeBase, declared_attr
import re

class Base(DeclarativeBase):
    @declared_attr.directive
    def __tablename__(cls) -> str:
        # CamelCase to snake_case
        return re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()

