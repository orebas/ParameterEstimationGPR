#!/bin/bash
# Overleaf Git Bridge Workflow Helper
# Manages bidirectional sync with Overleaf via Git

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_header() {
    echo ""
    echo "=================================================="
    echo "$1"
    echo "=================================================="
}

function print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

function print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

function print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check for command argument
if [ $# -eq 0 ]; then
    print_header "Overleaf Git Bridge Workflow"
    echo ""
    echo "Usage: $0 <command>"
    echo ""
    echo "Commands:"
    echo "  push    - Push current changes to Overleaf"
    echo "  pull    - Pull changes from Overleaf"
    echo "  sync    - Two-way sync (pull then push)"
    echo "  status  - Show sync status"
    echo "  init    - Initial setup of Overleaf branch"
    echo ""
    exit 0
fi

COMMAND=$1

case $COMMAND in
    "init")
        print_header "Initializing Overleaf Integration"

        # Check if overleaf remote exists
        if ! git remote | grep -q "overleaf"; then
            print_error "Overleaf remote not configured!"
            echo "Run ./overleaf_git_setup.sh first"
            exit 1
        fi

        # Create a clean branch for Overleaf
        echo "Creating clean Overleaf branch..."
        git checkout master
        git checkout -b overleaf-sync 2>/dev/null || {
            git checkout overleaf-sync
        }

        # Remove non-paper files from tracking
        echo "Configuring paper-only content..."

        # Create sparse checkout for paper files only
        cat > .overleaf-files << 'EOF'
paper/
!paper/*.pdf
.gitignore
README.md
EOF

        # Remove everything except paper files
        git rm -r --cached scripts/ dataset_package/ 2>/dev/null || true
        git rm -r --cached deprecated/ docs/ 2>/dev/null || true
        git rm -r --cached *.sh *.py 2>/dev/null || true
        git rm --cached pyproject.toml setup.sh 2>/dev/null || true

        # Keep only paper source
        git add paper/paper.tex paper/references.bib
        git add paper/tables/*.tex paper/figures/*.pdf 2>/dev/null || true

        git commit -m "Overleaf sync: paper files only" || {
            print_warning "No changes to commit"
        }

        print_success "Overleaf branch initialized"
        echo ""
        echo "Next: Run '$0 push' to send to Overleaf"
        ;;

    "push")
        print_header "Pushing to Overleaf"

        # Ensure we're on the right branch
        CURRENT_BRANCH=$(git branch --show-current)

        if [ "$CURRENT_BRANCH" != "overleaf-sync" ]; then
            echo "Switching to overleaf-sync branch..."
            git checkout overleaf-sync || {
                print_error "overleaf-sync branch not found. Run '$0 init' first"
                exit 1
            }
        fi

        # Merge latest changes from master (paper files only)
        echo "Merging latest paper changes from master..."
        git checkout master -- paper/paper.tex paper/references.bib 2>/dev/null
        git checkout master -- paper/tables/*.tex paper/figures/*.pdf 2>/dev/null || true

        # Regenerate if needed
        if [ -f ".venv/bin/activate" ]; then
            echo "Regenerating tables and figures..."
            source .venv/bin/activate
            python3 scripts/generate_corrected_tables_1_2.py 2>/dev/null || true
            python3 scripts/generate_system_performance_tables.py 2>/dev/null || true
            python3 scripts/generate_figure1_gpr_demo.py 2>/dev/null || true
            python3 scripts/generate_all_final_figures.py 2>/dev/null || true

            # Copy generated files
            if [ -d "outputs/tables" ]; then
                cp outputs/tables/*.tex paper/tables/ 2>/dev/null || true
            fi
            if [ -d "outputs/figures/corrected" ]; then
                cp outputs/figures/corrected/*.pdf paper/figures/ 2>/dev/null || true
            fi
        fi

        # Commit if there are changes
        git add paper/
        git commit -m "Update paper content for Overleaf $(date +%Y-%m-%d)" || {
            print_warning "No changes to push"
        }

        # Push to Overleaf
        echo "Pushing to Overleaf..."
        git push overleaf overleaf-sync:master --force || {
            print_error "Push failed. Check your Overleaf credentials."
            exit 1
        }

        print_success "Successfully pushed to Overleaf!"

        # Switch back to master
        git checkout master
        ;;

    "pull")
        print_header "Pulling from Overleaf"

        # Fetch from Overleaf
        echo "Fetching from Overleaf..."
        git fetch overleaf

        # Check out Overleaf's version
        git checkout overleaf-sync 2>/dev/null || git checkout -b overleaf-sync

        # Merge Overleaf changes
        echo "Merging Overleaf changes..."
        git merge overleaf/master --no-edit || {
            print_warning "Merge conflicts detected. Resolve manually."
        }

        # Copy paper source back to master
        echo "Updating master branch with text changes..."
        git checkout master
        git checkout overleaf-sync -- paper/paper.tex paper/references.bib

        # Commit changes
        git add paper/paper.tex paper/references.bib
        git commit -m "Sync text changes from Overleaf $(date +%Y-%m-%d)" || {
            print_warning "No text changes from Overleaf"
        }

        print_success "Successfully pulled from Overleaf!"
        ;;

    "sync")
        print_header "Two-way Sync with Overleaf"

        # Pull first
        $0 pull

        # Then push
        $0 push

        print_success "Sync complete!"
        ;;

    "status")
        print_header "Overleaf Sync Status"

        echo "Current branch: $(git branch --show-current)"
        echo ""

        echo "Overleaf remote:"
        git remote -v | grep overleaf || {
            print_error "Overleaf remote not configured"
        }
        echo ""

        echo "Recent sync commits:"
        git log --oneline -5 --grep="Overleaf\|overleaf" 2>/dev/null || {
            print_warning "No sync history found"
        }
        echo ""

        # Check for uncommitted changes
        if [ -n "$(git status --porcelain paper/)" ]; then
            print_warning "Uncommitted changes in paper/"
            git status -s paper/
        else
            print_success "Paper files are clean"
        fi
        ;;

    *)
        print_error "Unknown command: $COMMAND"
        echo "Run '$0' without arguments for help"
        exit 1
        ;;
esac