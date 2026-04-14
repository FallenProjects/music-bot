#!/bin/bash

# Copyright (c) 2025 AshokShau
# Licensed under the GNU AGPL v3.0

# Make it executable by : chmod +x setup.sh
# Run after cloning with: ./setup.sh

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

error_exit() {
    echo -e "${RED}Error: $1${NC}" >&2
    exit 1
}

validate_int() {
    if [[ ! "$1" =~ ^[0-9]+$ ]]; then
        error_exit "Please enter a valid integer for $2"
    fi
}

validate_url() {
    if [[ -n "$1" && ! "$1" =~ ^https?:// ]]; then
        error_exit "Please enter a valid URL for $2 (must start with http:// or https://)"
    fi
}

validate_bool() {
    local lower
    lower=$(echo "$1" | tr '[:upper:]' '[:lower:]')
    if [[ ! "$lower" =~ ^(true|false)$ ]]; then
        error_exit "Please enter either 'True' or 'False' for $2"
    fi
}

ask_env() {
    local var_name=$1
    local prompt=$2
    local default=$3
    local validate_func=$4
    local secret=$5
    local value

    while true; do
        if [ "$secret" = "true" ]; then
            read -s -p "$prompt [$default]: " value
            echo
        else
            read -p "$prompt [$default]: " value
        fi

        value=${value:-$default}

        if [ -n "$validate_func" ]; then
            $validate_func "$value" "$var_name" || continue
        fi
        break
    done

    echo "$value"
}

install_tgmusicbot() {
    echo -e "${GREEN}Starting TgMusicBot installation...${NC}"

    # Step 1: System Prep
    echo -e "${YELLOW}Updating system packages...${NC}"
    sudo apt-get update && sudo apt-get upgrade -y || error_exit "System update failed"

    echo -e "${YELLOW}Installing required tools...${NC}"
    sudo apt-get install git python3-pip ffmpeg tmux -y || error_exit "Failed to install required packages"

    # Step 2: Python Env
    echo -e "${YELLOW}Setting up Python environment...${NC}"
    pip3 install uv || error_exit "Failed to install uv"

    echo -e "${YELLOW}Creating virtual environment (.venv)...${NC}"
    uv venv || error_exit "Failed to create venv"

    # Auto-activate the venv
    if [ -f ".venv/bin/activate" ]; then
        echo -e "${GREEN}Activating virtual environment...${NC}"
        # shellcheck disable=SC1091
        source .venv/bin/activate || error_exit "Failed to activate venv"
    else
        error_exit ".venv/bin/activate not found"
    fi

    echo -e "${YELLOW}Installing dependencies via uv...${NC}"
    uv sync || error_exit "Dependency sync failed"

    # Step 3: Config
    echo -e "${YELLOW}Configuring environment variables...${NC}"
    [ -f sample.env ] && cp sample.env .env || touch .env

    API_ID=$(ask_env "API_ID" "Enter your Telegram API ID" "" validate_int)
    API_HASH=$(ask_env "API_HASH" "Enter your Telegram API Hash" "" "" "true")
    TOKEN=$(ask_env "TOKEN" "Enter your bot token" "" "" "true")
    MONGO_URI=$(ask_env "MONGO_URI" "Enter MongoDB URI" "" "")

    MIN_MEMBER_COUNT=$(ask_env "MIN_MEMBER_COUNT" "Enter minimum member count" "50" validate_int)
    OWNER_ID=$(ask_env "OWNER_ID" "Enter owner ID" "5938660179" validate_int)
    LOGGER_ID=$(ask_env "LOGGER_ID" "Enter logger ID" "-1002166934878" validate_int)

    SESSION_STRINGS=()
    echo -e "${YELLOW}Enter session strings (at least 1 required, up to 10):${NC}"
    for i in {1..10}; do
        STRING=$(ask_env "STRING$i" "  STRING$i (leave empty to stop)" "")
        [ -n "$STRING" ] && SESSION_STRINGS+=("$STRING") || break
    done
    if [ ${#SESSION_STRINGS[@]} -eq 0 ]; then
        error_exit "At least one STRING is required"
    fi

    API_URL=$(ask_env "API_URL" "Enter API URL" "https://api.fallenapi.fun" validate_url)
    API_KEY=$(ask_env "API_KEY" "Enter API key (leave empty if not using)" "" "" "true")
    PROXY=$(ask_env "PROXY" "Enter proxy URL (leave empty if not using)" "" validate_url)
    DEFAULT_SERVICE=$(ask_env "DEFAULT_SERVICE" "Enter default service" "youtube")
    DOWNLOADS_DIR=$(ask_env "DOWNLOADS_DIR" "Enter downloads directory" "database/music")
    SUPPORT_GROUP=$(ask_env "SUPPORT_GROUP" "Enter support group URL" "https://t.me/GuardxSupport" validate_url)
    SUPPORT_CHANNEL=$(ask_env "SUPPORT_CHANNEL" "Enter support channel URL" "https://t.me/FallenProjects" validate_url)
    START_IMG=$(ask_env "START_IMG" "Enter start image URL" "https://i.pinimg.com/1200x/e8/89/d3/e889d394e0afddfb0eb1df0ab663df95.jpg" validate_url)
    IGNORE_BACKGROUND_UPDATES=$(ask_env "IGNORE_BACKGROUND_UPDATES" "Ignore background updates? (True/False)" "True" validate_bool)
    AUTO_LEAVE=$(ask_env "AUTO_LEAVE" "Enable auto leave? (True/False)" "False" validate_bool)
    COOKIES_URL=$(ask_env "COOKIES_URL" "Enter cookies URL(s), comma or space separated" "")
    DEVS=$(ask_env "DEVS" "Enter developer IDs (space separated)" "")

    # Write .env
    echo -e "${YELLOW}Writing configuration to .env...${NC}"
    {
        echo "API_ID=\"$API_ID\""
        echo "API_HASH=\"$API_HASH\""
        echo "TOKEN=\"$TOKEN\""
        echo "MONGO_URI=\"$MONGO_URI\""
        echo "MIN_MEMBER_COUNT=\"$MIN_MEMBER_COUNT\""
        echo "OWNER_ID=\"$OWNER_ID\""
        echo "LOGGER_ID=\"$LOGGER_ID\""
        for i in "${!SESSION_STRINGS[@]}"; do
            echo "STRING$((i+1))=\"${SESSION_STRINGS[i]}\""
        done
        echo "API_URL=\"$API_URL\""
        [ -n "$API_KEY" ] && echo "API_KEY=\"$API_KEY\""
        [ -n "$PROXY" ] && echo "PROXY=\"$PROXY\""
        echo "DEFAULT_SERVICE=\"$DEFAULT_SERVICE\""
        echo "DOWNLOADS_DIR=\"$DOWNLOADS_DIR\""
        echo "SUPPORT_GROUP=\"$SUPPORT_GROUP\""
        echo "SUPPORT_CHANNEL=\"$SUPPORT_CHANNEL\""
        echo "START_IMG=\"$START_IMG\""
        echo "IGNORE_BACKGROUND_UPDATES=\"$IGNORE_BACKGROUND_UPDATES\""
        echo "AUTO_LEAVE=\"$AUTO_LEAVE\""
        [ -n "$COOKIES_URL" ] && echo "COOKIES_URL=\"$COOKIES_URL\""
        [ -n "$DEVS" ] && echo "DEVS=\"$DEVS\""
    } > .env

    echo -e "${GREEN}Installation complete!${NC}"
    echo -e "${YELLOW}To start the bot:${NC}"
    echo "tmux new -s musicbot"
    echo "tgmusic"
    echo
    echo -e "${YELLOW}Tmux tips:${NC}"
    echo "Detach: Ctrl+B then D"
    echo "Reattach: tmux attach -t musicbot"
    echo "Kill: tmux kill-session -t musicbot"
    echo
    echo -e "${YELLOW}⚡ Virtual environment is active. To use it later, run:${NC}"
    echo "source .venv/bin/activate"
}

install_tgmusicbot
