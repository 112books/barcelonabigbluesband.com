#!/bin/bash

# sync-bbbb.sh - Git + Hugo + Deploy complet (Barcelona Big Blues Band)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuració
REMOTE="origin"
BUILD_DIR="public"

# SSH/RSYNC (opcional) — dades al arxiu privat, no dins el repo
CONF_FILE="$HOME/.bbbb-deploy.conf"
if [ -f "$CONF_FILE" ]; then
    source "$CONF_FILE"
fi

# Caché npm local — evita errors de permisos a ~/.npm en cridar npx pagefind
export npm_config_cache="${TMPDIR:-/tmp}/npm-cache-bbbb"
mkdir -p "$npm_config_cache"

# Missatges
print_message() { echo -e "${BLUE}[sync-bbbb]${NC} $1"; }
print_success() { echo -e "${GREEN}[✓]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[!]${NC} $1"; }
print_error() { echo -e "${RED}[✗]${NC} $1"; }

# Branca actual o per defecte
current_branch() {
    git branch --show-current
}

# Verificar repo
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "No és un repositori Git"
        exit 1
    fi
}

# Info ràpida
show_header() {
    echo ""
    echo "======================================"
    echo " Projecte: $(basename $(pwd))"
    echo " Branca: $(current_branch)"
    echo "======================================"
    echo ""
}

# Estat
show_status() {
    print_message "Estat del repositori"
    echo ""
    if [[ -n $(git status -s) ]]; then
        print_warning "Canvis locals:"
        git status -s
    else
        print_success "Repositori net"
    fi
    echo ""
}

# Pull
do_pull() {
    local BRANCH=${1:-$(current_branch)}
    print_message "Pull ($BRANCH)..."
    git pull $REMOTE $BRANCH --rebase || exit 1
    print_success "Pull correcte"
}

# Sync: pull --rebase + push
do_sync() {
    local BRANCH=${1:-$(current_branch)}
    print_message "Sincronitzant amb el remot ($BRANCH)..."

    # Si hi ha canvis locals, fem commit primer
    if [[ -n $(git status -s) ]]; then
        print_warning "Canvis detectats:"
        git status -s
        echo ""
        read -p "Missatge del commit: " msg
        git add .
        git commit -m "$msg"
    fi

    # Pull --rebase per integrar canvis remots
    print_message "Pull --rebase per integrar canvis remots..."
    if ! git pull $REMOTE $BRANCH --rebase; then
        print_error "Error en el pull --rebase. Resol els conflictes i torna a intentar-ho."
        exit 1
    fi

    # Push
    print_message "Push..."
    if ! git push $REMOTE $BRANCH; then
        print_error "Error en el push."
        exit 1
    fi

    print_success "Push correcte"
    if [[ "$BRANCH" == "staging" ]]; then
        print_message "GitHub Pages farà deploy automàtic de staging"
    elif [[ "$BRANCH" == "main" ]]; then
        print_message "Cloudflare Pages farà deploy automàtic de producció"
    fi
}

# Push (compatibilitat)
do_push() {
    do_sync
}

# Genera índex Pagefind
do_pagefind() {
    local env=$1
    print_message "Generant índex Pagefind ($env)..."
    npx -y pagefind \
        --site ${BUILD_DIR} \
        --root-selector "main#main-content" \
        --exclude-selectors ".nav-compact,.site-header,footer,.concerts-past-section" \
        --output-subdir pagefind || exit 1
    print_success "Índex Pagefind generat"
}

# Build local de previsualització (staging)
do_build_local() {
    print_message "Build Hugo local (staging)..."
    rm -rf ${BUILD_DIR}
    hugo --minify --environment staging || exit 1
    if [ -f "${BUILD_DIR}/en/404.html" ]; then
        cp ${BUILD_DIR}/en/404.html ${BUILD_DIR}/404.html
    fi
    do_pagefind staging
    print_success "Build local completat (${BUILD_DIR}/)"
}

# Publish — per defecte Cloudflare Pages (push a main) o rsync opcional
do_publish() {
    print_warning "Publish: el desplegament oficial és via Cloudflare Pages (push a main)."
    if [ -n "$SSH_KEY" ] && [ -n "$SSH_USER" ] && [ -n "$SSH_HOST" ]; then
        print_message "Hi ha configuració rsync ($SSH_HOST) — publicació directa opcional."
        do_sync main
        print_message "Netejant build anterior..."
        rm -rf ${BUILD_DIR}
        print_message "Build Hugo producció..."
        hugo --minify --environment production || exit 1
        if [ -f "${BUILD_DIR}/en/404.html" ]; then
            cp ${BUILD_DIR}/en/404.html ${BUILD_DIR}/404.html
        fi
        do_pagefind production
        print_message "Enviant fitxers via rsync..."
        rsync -avz --delete --checksum --omit-dir-times \
            --chmod=Du=rwx,Dgo=rx,Fu=rw,Fgo=r \
            --exclude='.DS_Store' \
            --exclude='.DS_Store?' \
            --exclude='*.map' \
            --ignore-errors \
            -e "ssh -i ${SSH_KEY} -o StrictHostKeyChecking=no" \
            ${BUILD_DIR}/ ${SSH_USER}@${SSH_HOST}:${SSH_PATH}/
        RESULT=$?
        if [ $RESULT -eq 0 ] || [ $RESULT -eq 23 ]; then
            print_success "Web publicada via rsync"
        else
            print_error "Error en la pujada. Comprova la connexió SSH."
            exit 1
        fi
    else
        print_message "Sense rsync configurat ($CONF_FILE)."
        print_message "Fer: git checkout main && ./sync-bbbb.sh push → Cloudflare Pages fa la resta."
        do_sync main
    fi
}

# Force push
do_force() {
    local BRANCH=${1:-$(current_branch)}
    print_warning "Forçarà el repositori remot ($BRANCH)"
    read -p "Segur? (s/N): " confirm
    if [[ "$confirm" =~ ^[Ss]$ ]]; then
        git push $REMOTE $BRANCH --force-with-lease
        print_success "Force push completat"
    else
        print_message "Cancel·lat"
    fi
}

# Menú interactiu
interactive_menu() {
    show_header

    echo "Què vols fer?"
    echo ""
    echo "1) Status      → Veure estat del repositori"
    echo "2) Pull        → Descarregar canvis de GitHub"
    echo "3) Push        → Pujar canvis (branca actual)"
    echo "4) Build local → Build de previsualització"
    echo "5) Publish     → Publicar a producció (main)"
    echo "6) Force       → Forçar push (perillós)"
    echo "0) Sortir"
    echo ""

    read -p "Opció: " opt
    echo ""

    case $opt in
        1) show_status ;;
        2) do_pull ;;
        3) do_push ;;
        4) do_build_local ;;
        5)
            print_warning "Això farà push a main → desplegament a PRODUCCIÓ (Cloudflare Pages)"
            read -p "Segur? (s/N): " confirm
            if [[ "$confirm" =~ ^[Ss]$ ]]; then
                do_publish
            else
                print_message "Cancel·lat"
            fi
            ;;
        6) do_force ;;
        0)
            print_message "Sortint..."
            exit 0
            ;;
        *)
            print_error "Opció no vàlida"
            ;;
    esac
}

# Main
check_git_repo

if [ -z "$1" ]; then
    interactive_menu
else
    case $1 in
        status)  show_status ;;
        pull)    do_pull ;;
        push)    do_push ;;
        build)   do_build_local ;;
        publish) do_publish ;;
        force)   do_force ;;
        *)
            print_error "Opció no vàlida"
            echo "Ús: ./sync-bbbb.sh {status|pull|push|build|publish|force}"
            ;;
    esac
fi

print_message "Fi del procés"
