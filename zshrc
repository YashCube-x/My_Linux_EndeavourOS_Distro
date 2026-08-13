export PATH="$HOME/.local/bin:$PATH"

HISTSIZE=5000
SAVEHIST=5000
HISTFILE=~/.zsh_history
setopt SHARE_HISTORY
setopt HIST_IGNORE_DUPS

alias ls='ls --color=auto'
alias vi='nvim'
alias ide='antigravity-ide'
alias agy-ide='antigravity-ide'
alias update='yay -Syu'
alias cls='clear'
alias chrome='google-chrome-stable'


autoload -Uz compinit
compinit

bindkey '^[[A' history-search-backward
bindkey '^[[B' history-search-forward

eval "$(starship init zsh)"

# FZF Interactive History Search & Completion
source /usr/share/fzf/key-bindings.zsh 2>/dev/null || true
source /usr/share/fzf/completion.zsh 2>/dev/null || true
eval "$(zoxide init zsh 2>/dev/null)" || true



# Set UTF-8 locale and btop alias
export LC_ALL=en_IN.UTF-8
alias btop="btop --force-utf"

# Added by Antigravity CLI installer
export PATH="/home/suyash/.local/bin:$PATH"
