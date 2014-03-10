# A one-time conversion from SVN to Git

# svn2git fails with an error
# 2>&1 git branch --track "0.2.0" "remotes/svn/0.2.0"
#svn2git  http://svn.code.sf.net/p/bleachbit/code/ --exclude bonus --exclude misc --tags releases

# This method loses release history, but it keeps all the commits (except for the bonus and misc directories).
time git svn clone  http://svn.code.sf.net/p/bleachbit/code/trunk

# After conversion, push to Github
cd trunk
git remote add origin git@github.com:az0/bleachbit.git
git push origin master


# Repeat for misc
time git svn clone  http://svn.code.sf.net/p/bleachbit/code/misc
cd misc
git remote add origin git@github.com:az0/bleachbit-misc.git
git push origin master
