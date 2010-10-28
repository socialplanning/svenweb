rm -rf /tmp/svnrepo
rm -rf /tmp/svnco
svnadmin create /tmp/svnrepo
svn co file:///tmp/svnrepo /tmp/svnco
echo flunc -p ftests/ svenweb -D page_id=$1,page_id2=$2,rev_big=3,rev_small=2$4 $3
flunc -p ftests/ svenweb -D page_id=$1,page_id2=$2,rev_big=3,rev_small=2$4 $3
