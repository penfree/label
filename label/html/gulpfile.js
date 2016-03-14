var gulp = require("gulp");
var browserify = require("browserify");
var reactify = require("reactify");
var source = require("vinyl-source-stream");

gulp.task('diagnosis', function(){
      return browserify('./js/diagnosis.js')
             .transform(reactify)
             .bundle()
             .pipe(source('diagnosis.js'))
             .pipe(gulp.dest('dist'));
});
