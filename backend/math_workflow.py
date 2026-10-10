"""Compatibility entry point; use website_workflow.py for the website helper."""
import sys
import website_workflow

if __name__ == '__main__':
    try:
        website_workflow.main()
    except (KeyboardInterrupt, EOFError):
        print('\nClosed. Saved workflow files are preserved.')
else:
    # Preserve imports and existing callers as well as the old terminal command.
    sys.modules[__name__] = website_workflow
