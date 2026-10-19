#!/bin/sh
# Minimal Gradle wrapper launcher (gradle-wrapper.jar is committed)
DIR="$(cd "$(dirname "$0")" && pwd)"
exec java -cp "$DIR/gradle/wrapper/gradle-wrapper.jar" org.gradle.wrapper.GradleWrapperMain "$@"
