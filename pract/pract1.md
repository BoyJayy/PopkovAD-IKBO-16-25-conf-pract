# Практическая работа №1

## задача 1
```bash
grep -o '^[^:]*' /etc/passwd | sort
```
![alt text](image-1.png)
## задача 2
```bash
grep -v '^[[:space:]]*#' /etc/protocols | awk 'NF >= 2 {print $2, $1}' | sort -nr | head -5
```
![alt text](image.png)
## задача 3
```bash
cat > banner <<'EOF'
#!/bin/bash

if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <text>"
    exit 1
fi

text="$*"
width=$(( ${#text} + 2 ))

printf -v line '%*s' "$width" ''
line=${line// /-}

printf '+%s+\n' "$line"
printf '| %s |\n' "$text"
printf '+%s+\n' "$line"
EOF
```
после этого будет работать 
```bash

./banner

```

## задача 4

``` bass
grep -oE '[A-Za-z_][A-Za-z0-9_]*' hello.c | sort -u | tr '\n' ' '
``` 
-o выводить только найденные совпадения
-E использовать расширенные регулярные выражения
![alt text](image-2.png)
![alt text](image-3.png)
```bash
cat > identifiers <<'EOF'
#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <file>"
    exit 1
fi

grep -oE '[A-Za-z_][A-Za-z0-9_]*' "$1" | sort -u | tr '\n' ' '
echo
EOF
```
после работает так
![alt text](image-4.png)

