# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
# Functions
deactivate () {
	if [ -n "${_OLD_VIRTUAL_PATH:-}" ]
	then
		PATH="${_OLD_VIRTUAL_PATH:-}" 
		export PATH
		unset _OLD_VIRTUAL_PATH
	fi
	if [ -n "${_OLD_VIRTUAL_PYTHONHOME:-}" ]
	then
		PYTHONHOME="${_OLD_VIRTUAL_PYTHONHOME:-}" 
		export PYTHONHOME
		unset _OLD_VIRTUAL_PYTHONHOME
	fi
	hash -r 2> /dev/null
	if [ -n "${_OLD_VIRTUAL_PS1:-}" ]
	then
		PS1="${_OLD_VIRTUAL_PS1:-}" 
		export PS1
		unset _OLD_VIRTUAL_PS1
	fi
	unset VIRTUAL_ENV
	unset VIRTUAL_ENV_PROMPT
	if [ ! "${1:-}" = "nondestructive" ]
	then
		unset -f deactivate
	fi
}
dev () {
	local project=$1 
	create_session () {
		tmux new-session -d -s dev -n pytest "docker-compose run test sh -c \"cd ${project} && sh\"" \; new-window -n neovim "cd ~/Brian_Code/${project} && exec \$SHELL" \; select-window -t neovim \; attach-session -t dev
	}
	cd ~/Brian_Code && source .petroff/bin/activate
	if [ -n "$project" ]
	then
		if ! tmux has-session -t dev 2> /dev/null
		then
			create_session
		else
			tmux attach-session -t dev
		fi
	fi
}
# Shell Options
setopt nohashdirs
setopt login
# Aliases
alias -- as='ask -lr | less'
alias -- ask='python3 /Users/bianders/Brian_Code/ask/ask.py'
alias -- botvinnik_remote='ssh -p 2222 fishhouses@68.47.92.102'
alias -- caruana_remote='ssh -p 2227 bianders@68.47.92.102'
alias -- chroma_caruana='ssh -L 8001:localhost:8001 Caruana'
alias -- clip=pbcopy
alias -- cod='python /Users/bianders/Brian_Code/Leviathan/summarize/CoD.py'
alias -- code_helper='python3 /Users/bianders/Brian_Code/code_helper/code_helper.py -c'
alias -- countdocs='mongosh --eval "db = db.getSiblingDB('\''Courses'\''); var count = db.Course_Objects.countDocuments(); print('\''Number of documents:'\'', count);"'
alias -- curate='python3 /Users/bianders/Brian_Code/Curator/Curate.py'
alias -- curation='python3 /Users/bianders/Brian_Code/Course/Curation/Curation.py'
alias -- curriculum='python3 /Users/bianders/Brian_Code/Course/Curation/Curriculum.py'
alias -- dc=docker-compose
alias -- debug='ask -d'
alias -- dotfiles='git --git-dir=$HOME/.dotfiles.git --work-tree=$HOME'
alias -- dotfiles-backup='dotfiles add ~/.zshrc ~/.zprofile ~/.aliases.zsh ~/.secrets.zsh ~/.functions.zsh && dotfiles commit -m '\''Backup dotfiles'\'' && dotfiles push'
alias -- download_all='python3 /Users/bianders/Brian_Code/Course/downloads/download_all.py &'
alias -- firstcourse='python3 /Users/bianders/Brian_Code/Course/Curation/FirstCourse.py'
alias -- git_all=git_all.sh
alias -- gotham_remote='ssh -p 2226 tazzystar@68.47.92.102'
alias -- lens='python /Users/bianders/Brian_Code/Lens/Lens.py'
alias -- lev=leviathan
alias -- lg='clear && tail -f'
alias -- locate_up='sudo /usr/libexec/locate.updatedb'
alias -- lp='python3 /Users/bianders/Brian_Code/Course/Curation/LP.py'
alias -- ls='ls --color=auto'
alias -- magnus_remote='ssh -p 2223 bianders@68.47.92.102'
alias -- meta='python /Users/bianders/Brian_Code/metaprompt/meta.py'
alias -- mongo_caruana='ssh -L 27017:localhost:27017 Caruana'
alias -- mongo_caruana_remote='ssh -L 27017:localhost:27017 Caruana_Remote'
alias -- obsidian='cd /Volumes/Capablanca/Morphy/ && nvim .'
alias -- obsidian_to_botvinnik='rsync -arulv "/Users/bianders/Library/Mobile Documents/iCloud~md~obsidian/Documents/Morphy" /Volumes/Capablanca'
alias -- obsidian_to_petrosian='rsync -arulv /Volumes/Capablanca/Morphy "/Users/bianders/Library/Mobile Documents/iCloud~md~obsidian/Documents/"'
alias -- ollama_up='ssh -L 11434:localhost:11434 Caruana -N > ollama_ssh.log 2>&1 &; echo '\''Tunnel to Ollama established at 11434.'\'
alias -- otis_remote='ssh -p 2221 otis@68.47.92.102'
alias -- p=python
alias -- panpdf='pandoc --pdf-engine=xelatex -V mainfont="Arial"'
alias -- partner='python3 /Users/bianders/Brian_Code/Course/Curation/Partner.py'
alias -- pydoc='python -m pydoc'
alias -- remote_samba='ssh -p 2222 -L 44500:localhost:445 -L 13900:localhost:139 fishhouses@68.47.92.102'
alias -- rerank='python3 /Users/bianders/Brian_Code/Course/RAG/Reranking.py'
alias -- run-help=man
alias -- snapshot='awk '\''FNR==1{print "==> " FILENAME " <=="}1'\'
alias -- szp='source ~/.zprofile'
alias -- toc='python3 /Users/bianders/Brian_Code/Course/Curation/TOC.py'
alias -- topic='python3 /Users/bianders/Brian_Code/Course/Curation/Topic.py'
alias -- tra='python /Users/bianders/Brian_Code/Course/Transcript/Transcript.py'
alias -- tu='tutorialize -lr | less'
alias -- twig='python3 /Users/bianders/Brian_Code/twig/twig.py'
alias -- twigs='python3 /Users/bianders/Brian_Code/twig/twig.py -o'
alias -- v=nvim
alias -- vim=nvim
alias -- vnv='source .venv/bin/activate'
alias -- vzp='nvim ~/.zprofile'
alias -- which-command=whence
alias -- work='cd ~/Brian_Code/work'
# Check for rg availability
if ! command -v rg >/dev/null 2>&1; then
  alias rg='/opt/homebrew/Cellar/ripgrep/14.1.1/bin/rg'
fi
export PATH=/Users/bianders/Brian_Code/.petroff/bin\:/opt/homebrew/opt/postgresql\@16/bin\:/Users/bianders/Brian_Code\:/opt/homebrew/bin/\:/usr/local/bin\:/Library/Frameworks/Python.framework/Versions/3.12/bin\:/opt/homebrew/bin\:/opt/homebrew/sbin\:/usr/local/bin\:/System/Cryptexes/App/usr/bin\:/usr/bin\:/bin\:/usr/sbin\:/sbin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin\:/Library/TeX/texbin\:/Applications/Wireshark.app/Contents/MacOS\:/usr/local/linkedin/bin\:/usr/local/Homebrew/bin\:/opt/stdlibs/homebrew\:/Users/bianders/.local/bin\:/Users/bianders/Brian_Code/Siphon/.venv/bin\:/opt/homebrew/opt/postgresql\@16/bin\:/Users/bianders/Brian_Code\:/opt/homebrew/bin/\:/Library/Frameworks/Python.framework/Versions/3.12/bin\:/Applications/Ghostty.app/Contents/MacOS\:~/.local/share/nvim/mason/bin/\:~/.local/share/nvim/mason/bin/
