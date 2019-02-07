#!/bin/bash

sn=$1
cmd0=$2
cmd1=$3

SHELL="/bin/bash --noprofile --norc"
tmux new-session -s $sn -n etc -d $SHELL
tmux set-option -t $sn default-terminal "screen-256color"
tmux set-option -t $sn escape-time 0
tmux set-option -t $sn status off
tmux split-window -t $sn -h $SHELL
tmux set-option -t $sn pane-border-status top
tmux select-layout -t $sn even-horizontal

tmux set-option -t $sn pane-border-format "#T"
tmux set-option -t $sn pane-border-format "#T"
tmux select-pane -t $sn.0 -T $cmd0
tmux select-pane -t $sn.1 -T $cmd1
tmux send-keys -t $sn.0 "$cmd0 $cmd0.md" ENTER
tmux send-keys -t $sn.1 "$cmd1 $cmd1.md" ENTER
tmux set-window-option -t $sn synchronize-panes on

# ensure that neovim has started before we attach
sleep 0.5

tmux attach-session -t $sn
