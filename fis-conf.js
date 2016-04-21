
fis.set('project.ignore', [
    '.git/**',
    '.idea/**',
    "**.pyc",
    'build/**',
    'dist/**',
    "/dashboard/migrations/**",
    "/accounts/migrations/**",
    'fis-conf.js',
    'README.md'
]);

// 加 md5
fis.match('*.{js,css,png,jpg,gif}', {
    useHash: true
});

fis.match('*.js', {
    // fis-optimizer-uglify-js 插件进行压缩，已内置
    optimizer: fis.plugin('uglify-js',
        {
            output: {
                ascii_only: true
            },
            // 混淆
            mangle: true,
            compress: {
                // 不显示 console.log
                drop_console: true
                // 需要去掉的函数
                //pure_funcs: ['console.log']
            }
        })
});

fis.match('*.css', {
    // fis-optimizer-clean-css 插件进行压缩，已内置
    optimizer: fis.plugin('clean-css')
});

fis.match('*.png', {
    // fis-optimizer-png-compressor 插件进行压缩，已内置
    optimizer: fis.plugin('png-compressor')
});

// 对已经是min的js和css就不再压缩
fis.match('*.min.{js,css}', {
    optimizer: null
});

