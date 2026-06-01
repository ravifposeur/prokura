# Shared API Layer

Folder ini disiapkan untuk utilitas bersama antar service, seperti koneksi database, response helper, dan middleware.

Saat ini host API masih berada di `server.js`. Target refactor berikutnya adalah memindahkan `Pool` PostgreSQL dan helper HTTP ke folder ini agar setiap service module memakai dependensi yang sama secara eksplisit.
