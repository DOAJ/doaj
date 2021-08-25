var=0
while $1; do
    ((var++))
    echo "*** RETRY $var"
done