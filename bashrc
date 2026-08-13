#
# ~/.bashrc
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

alias ls='ls --color=auto'
alias grep='grep --color=auto'
alias update='yay -Syu'
alias cls='clear'
alias chrome='google-chrome-stable'
alias ide='antigravity-ide'
alias agy-ide='antigravity-ide'
PS1='[\u@\h \W]\$ '



# Set UTF-8 locale and btop alias
export LC_ALL=en_IN.UTF-8
alias btop="btop --force-utf"

# Added by Antigravity CLI installer
export PATH="/home/suyash/.local/bin:$PATH"

