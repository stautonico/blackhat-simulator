echo $1 | grep --quiet -e "403.html" -e "404.html"

if [ $? = 1 ]; then
    echo "Injecting theme into $1"
    echo "<style>$(cat dark_theme_inject.css)</style>" >> $1
fi
