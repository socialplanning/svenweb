rm -rf /tmp/svenweb
bzr init /tmp/svenweb
echo flunc -t http://localhost:5052 -p ftests/ svenweb -D page_id=joe-page,page_id2=moe-page,rev_big=3,rev_small=2$2 $1
flunc -t http://localhost:5052 -p ftests/ svenweb -D page_id=joe-page,page_id2=moe-page,rev_big=3,rev_small=2$2 $1
