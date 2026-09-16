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

``` 

``` bash =