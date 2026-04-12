"""
Script de migration automatique: print() -> logging

Remplace tous les print() statements par des appels logging appropriés.
"""
import re
from pathlib import Path


def migrate_file(filepath: Path) -> tuple[int, str]:
    """
    Migrate a single file from print() to logging.

    Returns:
        (number_of_replacements, new_content)
    """
    content = filepath.read_text(encoding='utf-8')
    original_content = content
    replacements = 0

    # Pattern 1: print(f"[TAG] Message")
    # -> logger.info("Message", extra={"tag": "TAG"})
    pattern1 = r'print\(f"\[([A-Z_\s]+)\]\s*([^"]+)"\)'

    def replace_tagged(match):
        nonlocal replacements
        replacements += 1
        tag = match.group(1).strip()
        message = match.group(2)

        # Determine log level based on tag
        if any(x in tag for x in ['ERROR', 'FAIL', 'CRITICAL']):
            level = 'error'
        elif any(x in tag for x in ['WARNING', 'WARN']):
            level = 'warning'
        elif any(x in tag for x in ['DEBUG']):
            level = 'debug'
        else:
            level = 'info'

        # Clean up message (remove extra braces if any)
        return f'logger.{level}("{message}", extra={{"tag": "{tag}"}})'

    content = re.sub(pattern1, replace_tagged, content)

    # Pattern 2: print(f"Message {var}")
    # -> logger.info(f"Message {var}")
    pattern2 = r'print\(f"([^"]+)"\)'

    def replace_fstring(match):
        nonlocal replacements
        replacements += 1
        message = match.group(1)

        # Determine level based on keywords
        msg_lower = message.lower()
        if any(x in msg_lower for x in ['error', 'fail', 'critical']):
            level = 'error'
        elif any(x in msg_lower for x in ['warning', 'warn']):
            level = 'warning'
        elif any(x in msg_lower for x in ['debug']):
            level = 'debug'
        else:
            level = 'info'

        return f'logger.{level}(f"{message}")'

    content = re.sub(pattern2, replace_fstring, content)

    # Pattern 3: print("Simple message")
    pattern3 = r'print\("([^"]+)"\)'

    def replace_simple(match):
        nonlocal replacements
        replacements += 1
        message = match.group(1)
        return f'logger.info("{message}")'

    content = re.sub(pattern3, replace_simple, content)

    # Add logger import at top if replacements were made
    if replacements > 0 and 'from app.logger import get_logger' not in content:
        # Find the last import statement
        import_lines = []
        other_lines = []
        in_imports = True

        for line in content.split('\n'):
            if in_imports:
                if line.startswith('import ') or line.startswith('from '):
                    import_lines.append(line)
                elif line.strip() == '':
                    import_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)
            else:
                other_lines.append(line)

        # Add logger import after other app imports
        import_lines.append('')
        import_lines.append('from app.logger import get_logger')
        import_lines.append(f'logger = get_logger(__name__)')
        import_lines.append('')

        content = '\n'.join(import_lines + other_lines)

    return replacements, content


def main():
    """Migrate all Python files in app/ directory."""
    app_dir = Path("app")

    if not app_dir.exists():
        print("ERROR: app/ directory not found")
        return

    total_replacements = 0
    files_modified = 0

    # Migrate all .py files except __init__.py and logger.py
    for filepath in app_dir.glob("*.py"):
        if filepath.name in ['__init__.py', 'logger.py']:
            continue

        print(f"\nProcessing {filepath.name}...")
        replacements, new_content = migrate_file(filepath)

        if replacements > 0:
            # Write back
            filepath.write_text(new_content, encoding='utf-8')
            print(f"  [OK] {replacements} print() statements replaced")
            total_replacements += replacements
            files_modified += 1
        else:
            print(f"  - No print() statements found")

    print(f"\n{'='*60}")
    print(f"MIGRATION COMPLETE")
    print(f"{'='*60}")
    print(f"Files modified: {files_modified}")
    print(f"Total replacements: {total_replacements}")
    print(f"\nNext steps:")
    print(f"1. Review changes with: git diff")
    print(f"2. Test with: python tests/test_v5_calibrated.py")
    print(f"3. Set log level with: export LOG_LEVEL=DEBUG (or INFO/WARNING/ERROR)")


if __name__ == "__main__":
    main()
