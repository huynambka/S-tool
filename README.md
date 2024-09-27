# S-tool

-   Một công cụ tự động detect và khai thác lỗ hổng SSTI (Hiện tại chỉ áp dụng cho SpEL)

# Cách sử dụng

-   Ví dụ:

```
python3 src/main.py --url 'http://127.0.0.1:1337/addContact' --params '{"firstName":"Shiba","lastName":"Jutsu","description":"Handsome","country":"Vietnam"}' --method POST
```

[![asciicast](https://asciinema.org/a/eFVT7G16Rj6TLjwXaT5H5TRSS.svg)](https://asciinema.org/a/eFVT7G16Rj6TLjwXaT5H5TRSS)

-   Tạo payload với WAF trong file waf.json

```
python3 src/main.py --exec id --waf waf.json
```

# How it works
