# Snapshot file
# Unset all aliases to avoid conflicts with functions
unalias -a 2>/dev/null || true
# Functions
brew () {
	afplay ~/Sounds/pouring-beer-1.mp3 > /dev/null 2>&1 &
	disown
	command brew "$@"
}
cddev () {
	local root
	root=$(_get_git_root)  || return 1
	local dev_dir="$root/dev" 
	if [[ ! -d "$dev_dir" ]]
	then
		echo "No dev/ directory found at $root" >&2
		return 1
	fi
	cd "$dev_dir" || return
}
cddocs () {
	local root
	root=$(_get_git_root)  || return 1
	local docs_dir="$root/docs" 
	if [[ ! -d "$docs_dir" ]]
	then
		echo "No docs/ directory found at $root" >&2
		return 1
	fi
	cd "$docs_dir" || return
}
cdin () {
	shopt -s dotglob nullglob
	local dirs=(*/) 
	shopt -u dotglob
	if [ ${#dirs[@]} -eq 0 ] || [ ! -d "${dirs[0]}" ]
	then
		echo "No directories found"
		return 1
	fi
	cd "${dirs[0]}" || return
}
cdpkg () {
	local root
	root=$(_get_git_root)  || return 1
	local pkg_dir
	pkg_dir=$(find "$root/src" -mindepth 1 -maxdepth 1 -type d | head -n 1) 
	if [[ -z "$pkg_dir" ]]
	then
		echo "No directory found in src/" >&2
		return 1
	fi
	cd "$pkg_dir" || return
}
cdroot () {
	local root
	root=$(_get_git_root)  || return 1
	cd "$root" || return
}
cdtests () {
	local root
	root=$(_get_git_root)  || return 1
	local test_dir="$root/tests" 
	if [[ ! -d "$test_dir" ]]
	then
		echo "No tests/ directory found at $root" >&2
		return 1
	fi
	cd "$test_dir" || return
}
conduit () {
	afplay ~/Sounds/conduit.mp3 > /dev/null 2>&1 &
	disown
	command conduit "$@"
}
curate () {
	afplay ~/Sounds/curate.mp3 > /dev/null 2>&1 &
	disown
	command curate "$@"
}
deps () {
	if [ -z "$1" ]
	then
		echo "Usage: deps <module_name>"
		return 1
	fi
	python -v -m "$1" 2>&1 | grep "^import" | sort -u
}
envrc () {
	cat <<'EOF' > .envrc
# .envrc

# --- Project Path Exports ---
export PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [[ -z "$PROJECT_ROOT" ]]; then
  echo "direnv: error: could not find git root." >&2
  exit 1
fi

export DEV="$PROJECT_ROOT/dev"
export DOCS="$PROJECT_ROOT/docs"
export TESTS="$PROJECT_ROOT/tests"

MAIN_PKG_DIR=$(find "$PROJECT_ROOT/src" -mindepth 1 -maxdepth 1 -type d | head -n 1)
if [[ -d "$MAIN_PKG_DIR" ]]; then
    export PACK="$MAIN_PKG_DIR"
fi

# --- Virtual Env Activation ---
deactivate 2>/dev/null || true
source .venv/bin/activate
EOF
	echo "Created .envrc. Run 'direnv allow' to activate."
}
flatten () {
	afplay ~/Sounds/flatten.mp3 > /dev/null 2>&1 &
	disown
	command flatten "$@"
}
get () {
	afplay ~/Sounds/get.mp3 > /dev/null 2>&1 &
	disown
	command get "$@"
}
giti () {
	cat > .gitignore <<'EOF'
# Universal
__pycache__/
.pytest_cache/
.mypy_cache/
*.py[cod]
*$py.class
*.egg-info/
*.db
.env
.DS_Store
.python-version
*.log
*.sqlite3
.venv
uv.lock
EOF
	echo ".gitignore created in $(pwd)"
}
mkpyproj () {
	if [ -z "${1:-}" ]
	then
		echo "Usage: mkpyproj <package_name>" >&2
		return 1
	fi
	local pkg="$1" 
	command -v uv > /dev/null 2>&1 || {
		echo "uv not found on PATH"
		return 1
	}
	command -v git > /dev/null 2>&1 || {
		echo "git not found on PATH"
		return 1
	}
	[ -d .git ] || {
		git init > /dev/null && echo "✓ git init"
	}
	if [ ! -f pyproject.toml ]
	then
		uv init > /dev/null && echo "✓ uv init"
	else
		echo "• pyproject.toml exists (skip uv init)"
	fi
	[ ! -f main.py ] || {
		rm -f main.py && echo "✓ removed main.py"
	}
	mkdir -p "src/$pkg"
	[ -f "src/$pkg/__init__.py" ] || printf "__all__ = []\n" > "src/$pkg/__init__.py"
	if [ ! -f "src/$pkg/__main__.py" ]
	then
		cat > "src/$pkg/__main__.py" <<EOF
def main() -> None:
    print("hello from $pkg")
if __name__ == "__main__":
    main()
EOF
	fi
	[ -f "src/$pkg/py.typed" ] || : > "src/$pkg/py.typed"
	echo "✓ created src/$pkg/ (with py.typed)"
	mkdir -p tests
	if [ ! -f tests/test_basic.py ]
	then
		cat > tests/test_basic.py <<'EOF'
def test_sanity():
    assert True
EOF
		echo "✓ created tests/test_basic.py"
	else
		echo "• tests/test_basic.py exists"
	fi
	[ -d .venv ] || {
		uv venv > /dev/null && echo "✓ uv venv"
	}
	if [ -f .envrc ]
	then
		echo "• .envrc exists"
	else
		if command -v envrc > /dev/null 2>&1
		then
			envrc && echo "✓ created .envrc via envrc"
		else
			echo "• envrc helper not found (skipping .envrc)"
		fi
	fi
	direnv allow
	echo "✓ direnv allow"
	if [ -f .gitignore ]
	then
		echo "• .gitignore exists"
	else
		if typeset -f giti > /dev/null 2>&1
		then
			giti && echo "✓ wrote .gitignore"
		else
			echo "• giti function not found (skipping .gitignore)"
		fi
	fi
	pypr "$pkg"
	echo "✅ Done at $(pwd)"
	uv sync --editable
	echo "✓ uv sync --editable"
	echo "Project setup complete. Start coding in src/$pkg and run tests with 'pytest'."
}
morgan () {
	afplay ~/Sounds/morgan.mp3 > /dev/null 2>&1 &
	disown
	command morgan "$@"
}
note () {
	afplay ~/Sounds/scribble.wav > /dev/null 2>&1 &
	disown
	command note "$@"
}
pass_alias () {
	local alias="$1" 
	if [[ -z "$alias" ]]
	then
		echo "Usage: pass_alias_insert <email-alias>"
		return 1
	fi
	local service="${alias%%.*}" 
	if [[ -z "$service" ]]
	then
		echo "Error: could not determine service name from alias"
		return 1
	fi
	local pass_path="alias/$service" 
	local password
	if ! password="$(passwords)" 
	then
		echo "Error: password generation failed"
		return 1
	fi
	if [[ -z "$password" ]]
	then
		echo "Error: password generator returned empty result"
		return 1
	fi
	local username
	if ! username="$(usernames)" 
	then
		echo "Error: username generation failed"
		return 1
	fi
	if [[ -z "$username" ]]
	then
		echo "Error: username generator returned empty result"
		return 1
	fi
	printf "%s\n%s\n%s\n" "$password" "$alias" "$username" | pass insert --force --multiline "$pass_path" > /dev/null
	echo "Updated pass entry:"
	echo "  Path:     $pass_path"
	echo "  Email:    $alias"
	echo "  Username: $username"
}
pypr () {
	if [ -z "${1:-}" ]
	then
		echo "Usage: pypr <package_name>" >&2
		return 1
	fi
	local pkg="$1" 
	if [ ! -f pyproject.toml ]
	then
		cat > pyproject.toml <<EOF
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "$pkg"
version = "0.1.0"
EOF
		echo "✓ created pyproject.toml"
	fi
	if ! grep -q '^\[build-system\]' pyproject.toml
	then
		local _tmp
		_tmp="$(mktemp)" 
		cat > "$_tmp" <<'EOF'
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
EOF
		cat pyproject.toml >> "$_tmp"
		mv "$_tmp" pyproject.toml
		echo "✓ added [build-system] hatchling"
	else
		echo "• [build-system] exists"
	fi
	if grep -q '^\[project\]' pyproject.toml
	then
		if grep -q '^name\s*=' pyproject.toml
		then
			sed -i.bak -E "0,/^name\s*=.*/s//name = \"$pkg\"/" pyproject.toml && rm -f pyproject.toml.bak
			echo "✓ set project.name = \"$pkg\""
		else
			awk -v pkg="$pkg" '
        {print}
        /^\[project\]$/ && !added {print "name = \"" pkg "\""; added=1}
      ' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml
			echo "✓ inserted project.name = \"$pkg\""
		fi
	else
		cat >> pyproject.toml <<EOF
[project]
name = "$pkg"
version = "0.1.0"
EOF
		echo "✓ created [project] with name/version"
	fi
	if grep -q '^\[tool\.hatch\.build\.targets\.wheel\]' pyproject.toml
	then
		awk -v pkg="$pkg" '
      BEGIN{inwheel=0}
      /^\[tool\.hatch\.build\.targets\.wheel\]/{inwheel=1}
      /^\[/{if($0 !~ /\[tool\.hatch\.build\.targets\.wheel\]/) inwheel=0}
      {
        if(inwheel && $0 ~ /^packages\s*=/){
          print "packages = [\"src/" pkg "\"]"; next
        }
        print
      }
    ' pyproject.toml > pyproject.toml.tmp && mv pyproject.toml.tmp pyproject.toml
		awk '
      BEGIN{inwheel=0; has=0}
      /^\[tool\.hatch\.build\.targets\.wheel\]/{inwheel=1}
      /^\[/{if($0 !~ /\[tool\.hatch\.build\.targets\.wheel\]/) inwheel=0}
      { if(inwheel && $0 ~ /^sources\s*=\s*\["src"\]/) has=1; print > "pyproject.toml.tmp" }
      END{ if(!has){ print "sources = [\"src\"]" >> "pyproject.toml.tmp" } }
    ' pyproject.toml
		mv pyproject.toml.tmp pyproject.toml
	else
		cat >> pyproject.toml <<EOF
[tool.hatch.build.targets.wheel]
packages = ["src/$pkg"]
sources = ["src"]
EOF
	fi
	awk -v pkg="$pkg" '
    BEGIN{in=0; has=0}
    /^\[tool\.hatch\.build\.targets\.wheel\]/{in=1}
    /^\[/{if($0 !~ /\[tool\.hatch\.build\.targets\.wheel\]/) in=0}
    {
      if(in && $0 ~ /^include\s*=\s*\[/){inc=1}
      if(in && inc && $0 ~ /]/){inc=0}
      if(in && $0 ~ /src\/[^"]*\/py\.typed/){has=1}
      print > "pyproject.toml.tmp"
    }
    END{
      if(!has){
        print "py.typed not found in wheel include -> adding" > "/dev/stderr"
        print "include = [\"src/" pkg "/py.typed\"]" >> "pyproject.toml.tmp"
      }
    }
  ' pyproject.toml 2> /dev/null
	mv pyproject.toml.tmp pyproject.toml
	if ! grep -q '^\[tool\.hatch\.build\.targets\.sdist\]' pyproject.toml
	then
		cat >> pyproject.toml <<EOF
[tool.hatch.build.targets.sdist]
include = ["src/$pkg/py.typed"]
EOF
	else
		awk -v pkg="$pkg" '
      BEGIN{ins=0; has=0}
      /^\[tool\.hatch\.build\.targets\.sdist\]/{ins=1}
      /^\[/{if($0 !~ /\[tool\.hatch\.build\.targets\.sdist\]/) ins=0}
      {
        if(ins && $0 ~ /src\/[^"]*\/py\.typed/){has=1}
        print > "pyproject.toml.tmp"
      }
      END{
        if(!has){
          print "include = [\"src/" pkg "/py.typed\"]" >> "pyproject.toml.tmp"
        }
      }
    ' pyproject.toml
		mv pyproject.toml.tmp pyproject.toml
	fi
	echo "✓ configured hatch wheel/sdist targets (src/$pkg, py.typed)"
}
python () {
	afplay ~/Sounds/snake.mp3 > /dev/null 2>&1 &
	disown
	command python "$@"
}
siphon () {
	afplay ~/Sounds/sip-85917.mp3 > /dev/null 2>&1 &
	disown
	command siphon "$@"
}
ssh () {
	TERM=xterm-256color command ssh "$@"
}
tap () {
	afplay ~/Sounds/tap.mp3 > /dev/null 2>&1 &
	disown
	command tap "$@"
}
twig () {
	afplay ~/Sounds/twig-snap-classic-85662.mp3 > /dev/null 2>&1 &
	disown
	command twig "$@"
}
venv_info () {
	if [[ -n $VIRTUAL_ENV ]]
	then
		echo "($(basename $VIRTUAL_ENV)) "
	fi
}
# Shell Options
setopt nohashdirs
setopt login
setopt promptsubst
# Aliases
alias -- alphablue='ssh alphablue'
alias -- aptup='sudo apt update && sudo apt upgrade -y'
alias -- bc='cd /Users/bianders/Brian_Code/'
alias -- botvinnik='ssh botvinnik'
alias -- brewup='brew update && brew upgrade && brew cleanup'
alias -- cache='cd $HOME/.cache'
alias -- caruana='ssh caruana'
alias -- cd.='cd ..'
alias -- cd..='cd ../..'
alias -- cd...='cd ../../..'
alias -- cd....='cd ../../../..'
alias -- cdaquifer='cd /Users/bianders/Brian_Code/aquifer-project/src/aquifer'
alias -- cdask='cd /Users/bianders/Brian_Code/ask-project/src/ask'
alias -- cdconduit='cd /Users/bianders/Brian_Code/conduit-project/src/conduit'
alias -- cdcorsair='cd /Users/bianders/Brian_Code/corsair-project/src/corsair'
alias -- cdd=cddev
alias -- cddot='cd /Users/bianders/.dotfiles'
alias -- cdhaddock='cd /Users/bianders/Brian_Code/haddock-project/src/haddock'
alias -- cdheadwater='cd /Users/bianders/Brian_Code/headwater'
alias -- cdkramer='cd /Users/bianders/Brian_Code/kramer-project/src/kramer'
alias -- cdmentor='cd /Users/bianders/Brian_Code/mentor-project/src/mentor'
alias -- cdmeta='cd /Users/bianders/Brian_Code/metaprompt-project/src/metaprompt'
alias -- cdmorgan='cd /Users/bianders/Brian_Code/morgan-project/src/morgan'
alias -- cdp=cdpkg
alias -- cdpipelines='cd /Users/bianders/Brian_Code/pipelines-project/src/pipelines'
alias -- cdr=cdroot
alias -- cdsiphon='cd /Users/bianders/Brian_Code/siphon'
alias -- cdt=cdtests
alias -- cdtap='cd /Users/bianders/Brian_Code/tap-project/src/tap'
alias -- cdtrmnl='cd /Users/bianders/Brian_Code/trmnl-project/src/trmnl'
alias -- cdutils='cd /Users/bianders/Brian_Code/utils-project/src/utils'
alias -- cdwaterworks='cd /Users/bianders/Brian_Code/waterworks-project/src/waterworks'
alias -- cdwinnow='cd /Users/bianders/Brian_Code/winnow-project/src/winnow'
alias -- cdww='cd /Users/bianders/Brian_Code/waterworks-project/src/waterworks'
alias -- cheet='ssh cheet'
alias -- cld='cd /Users/bianders/.claude/'
alias -- clip=pbcopy
alias -- config='cd /Users/bianders/.config'
alias -- cputop='ps auxf | sort -nr -k 3 | head -10'
alias -- cs='cd src'
alias -- csin='cd src && cdin'
alias -- da='direnv allow'
alias -- dc='docker compose'
alias -- dcup='docker compose up --build'
alias -- dnfup='sudo dnf upgrade --refresh -y'
alias -- documents='cd /Users/bianders/Documents'
alias -- dotfiles='cd $HOME/.dotfiles && git status'
alias -- dotpull='cd /Users/bianders/.dotfiles && git pull && exec /bin/zsh -l'
alias -- dotpush='cd $HOME/.dotfiles && git add . && git commit -m "$(date +%Y-%m-%d)" && git push'
alias -- downloads='cd /Users/bianders/Downloads'
alias -- fnd='find . -iname "*$1*" 2>/dev/null'
alias -- fonts='cd /usr/share/fonts'
alias -- ga='git add .'
alias -- gb='git branch'
alias -- gc='git commit -m '
alias -- gi='git init'
alias -- gita=git_all
alias -- gitall=git_all
alias -- gits=git_status
alias -- gitstatus=git_status
alias -- gl='git log --oneline --graph --decorate -20'
alias -- gotham='ssh gotham'
alias -- gp='git pull'
alias -- gpush='git push'
alias -- gr='ghostty --reload-config'
alias -- grc='git rebase --continue'
alias -- gs='git status'
alias -- h='history | grep'
alias -- haddock='python -i -c "from haddock import Table;"'
alias -- hdwa='cd /Users/bianders/Brian_Code/headwater/headwater-api/src/headwater_api'
alias -- hdwc='cd /Users/bianders/Brian_Code/headwater/headwater-client/src/headwater_client'
alias -- hdws='cd /Users/bianders/Brian_Code/headwater/headwater-server/src/headwater_server'
alias -- hh='history | awk '\''{print $2}'\'' | sort | uniq -c | sort -rn | head -20'
alias -- home='cd /Users/bianders'
alias -- images='cd /mnt/nas/generated_images'
alias -- in=cdin
alias -- larsen='ssh larsen'
alias -- localip='ip addr show | grep '\''inet '\'' | grep -v 127.0.0.1 | awk '\''{print $2}'\'' | cut -d/ -f1'
alias -- locate_up='sudo /usr/libexec/locate.updatedb'
alias -- ls='ls --color=auto'
alias -- lsbiggest='ls -Sah | head -n 10'
alias -- lsd='ls -d */'
alias -- lsl='du -ah . | sort -rh | head -n 10'
alias -- lslatest='ls -Art | tail -n 1'
alias -- lsr='ls -Art | tail -n 10'
alias -- lss='ls -a'
alias -- memtop='ps auxf | sort -nr -k 4 | head -10'
alias -- morphy='cd /Users/bianders/morphy'
alias -- morphypull='cd /Users/bianders/morphy && git pull'
alias -- morphypush='cd $HOME/morphy && git add . && git commit -m "$(date +%Y-%m-%d)" && git push'
alias -- nas='cd /mnt/nas'
alias -- now='date '\''+%Y-%m-%d %H:%M:%S'\'
alias -- otis='ssh otis'
alias -- out='cd ..'
alias -- p=python
alias -- panpdf='pandoc --pdf-engine=xelatex -V mainfont="Arial"'
alias -- passpull='cd /Users/bianders/.password-store && git pull'
alias -- passpush='cd $HOME/.password-store && git add . && git commit -m "$(date +%Y-%m-%d)" && git push'
alias -- pdebug='PYTHON_LOG_LEVEL=3 python'
alias -- petrosian='ssh petrosian'
alias -- pi='python -i'
alias -- pictures='cd /Users/bianders/Pictures'
alias -- pinfo='PYTHON_LOG_LEVEL=2 python'
alias -- podcasts='cd /Users/bianders/Podcasts'
alias -- ports='ss -tulanp'
alias -- psql='psql -d postgres'
alias -- ptime='python -X importtime'
alias -- publicip='curl -s https://ifconfig.me -4'
alias -- pwarning='PYTHON_LOG_LEVEL=1 python'
alias -- pydoc='python -m pydoc'
alias -- pyp='cdr && v pyproject.toml'
alias -- pytest='python -m pytest'
alias -- readme='flatten . -d -v v > README.md'
alias -- run-help=man
alias -- sandbox='cd /Users/bianders/Brian_Code/sandbox'
alias -- scripts='cd /Users/bianders/.local/bin'
alias -- share='cd $HOME/.local/share'
alias -- siphon-debug='SIPHON_LOG_LEVEL=3 python -m siphon_server'
alias -- siphon-haiku='SIPHON_DEFAULT_MODEL=haiku python -m siphon_server'
alias -- siphon-nocache='SIPHON_CACHE=false python -m siphon_server'
alias -- siphon-test='LOG_LEVEL=3 CACHE=false python -m siphon_server'
alias -- siphona='cd /Users/bianders/Brian_Code/siphon/siphon-api/src/siphon_api'
alias -- siphonc='cd /Users/bianders/Brian_Code/siphon/siphon-client/src/siphon_client'
alias -- siphons='cd /Users/bianders/Brian_Code/siphon/siphon-server/src/siphon_server'
alias -- sizeof='du -sh * | sort -h'
alias -- skills='cd /Users/bianders/.config/conduit/skills'
alias -- spassky='ssh spassky'
alias -- src='exec /bin/zsh -l'
alias -- sshconfig='nvim /Users/bianders/.ssh/config'
alias -- state='cd $HOME/.local/state'
alias -- szp='source ~/.zprofile'
alias -- tailf='clear && tail -f'
alias -- tip='touch __init__.py'
alias -- torchver='uv run python -c "import torch; print(torch.__version__)"'
alias -- tre='tree -aC -I '\''.git|node_modules|.venv|__pycache__|.pytest_cache'\'' --dirsfirst -L 3'
alias -- typ='touch py.typed'
alias -- ue='uv tool install --editable .'
alias -- update_examples='cp example.py /Users/bianders/Brian_Code/siphon/siphon-server/src/siphon_server && cp example.py /Users/bianders/Brian_Code/siphon/siphon-api/src/siphon_api'
alias -- us='uv sync --editable --dev'
alias -- v=nvim
alias -- val='nvim /Users/bianders/.aliases'
alias -- vcal='nvim /Users/bianders/.custom_aliases'
alias -- vcex='nvim /Users/bianders/.custom_exports'
alias -- vd=deactivate
alias -- vex='nvim /Users/bianders/.exports'
alias -- vim=nvim
alias -- vnv='source .venv/bin/activate'
alias -- vrc='nvim ~/.zshrc'
alias -- vzp='nvim ~/.zprofile'
alias -- wallpapers='cd /Users/bianders/Pictures/Wallpapers'
alias -- wgdown='sudo nmcli connection down wg0'
alias -- wgup='sudo nmcli connection up wg0'
alias -- which-command=whence
alias -- work='cd /Users/bianders/Brian_Code/work'
alias -- z='_z 2>&1'
# Check for rg availability
if ! (unalias rg 2>/dev/null; command -v rg) >/dev/null 2>&1; then
  alias rg='/Users/bianders/.local/share/claude/versions/2.1.38 --ripgrep'
fi
export PATH=/Users/bianders/.cache/uv/environments-v2/batch-runner-9ff11284d0ffee40/bin\:/Users/bianders/Brian_Code/sandbox/.venv/bin\:/Users/bianders/.local/bin\:/Users/bianders/.volta/bin\:/Users/bianders/.npm-global/bin\:/Users/bianders/.cargo/bin\:/Users/bianders/.local/bin\:/Users/bianders/.volta/bin\:/Users/bianders/.npm-global/bin\:/Users/bianders/.cargo/bin\:/Library/Frameworks/Python.framework/Versions/3.12/bin\:/opt/homebrew/bin\:/opt/homebrew/sbin\:/usr/local/bin\:/System/Cryptexes/App/usr/bin\:/usr/bin\:/bin\:/usr/sbin\:/sbin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/local/bin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/bin\:/var/run/com.apple.security.cryptexd/codex.system/bootstrap/usr/appleinternal/bin\:/opt/pmk/env/global/bin\:/Library/TeX/texbin\:/Applications/Wireshark.app/Contents/MacOS\:/usr/local/linkedin/bin\:/usr/local/Homebrew/bin\:/opt/stdlibs/homebrew\:/Users/bianders/.local/bin\:/Users/bianders/.volta/bin\:/Users/bianders/.npm-global/bin\:/Users/bianders/.cargo/bin\:/Library/Frameworks/Python.framework/Versions/3.12/bin\:/Applications/Ghostty.app/Contents/MacOS
