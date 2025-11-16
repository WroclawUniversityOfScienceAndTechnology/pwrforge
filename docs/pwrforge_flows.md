# pwrforge flows

## New Project x86 dev flow

```console
pwrforge -h
pwrforge new -h
pwrforge new my_project --target x86
cd my_project
git status
git add .
git commit -m 'Initial commit'
pwrforge docker run
pwrforge build
pwrforge check
pwrforge test
pwrforge run
exit
```

## New Project esp32 dev flow

```console
pwrforge -h
pwrforge new -h
pwrforge new my_project_esp32 --target esp32
cd my_project_esp32
git add .
git commit -m 'Initial commit'
pwrforge docker run
idf.py menuconfig
pwrforge build
pwrforge gen --fs
pwrforge check
pwrforge test
pwrforge flash -h
pwrforge flash
pwrforge flash --fs
idf.py -B build/Debug monitor
ctrl+]
exit
```


## New Project stm32 dev flow

```console
pwrforge -h
pwrforge new -h
pwrforge new my_project_stm32 --target stm32
cd my_project_stm32
git add .
git commit -m 'Initial commit'
pwrforge docker run
pwrforge build
pwrforge check
pwrforge test
#pwrforge flash
exit
```

## Clean and build x86

```console
pwrforge docker run
ls ./build
pwrforge clean
ls ./build
pwrforge build --profile Debug
pwrforge build --profile Release
ls ./build
./build/Release/bin/my_project
./build/Debug/bin/my_project
exit
```

## Check and fix x86

```console
pwrforge docker run
vi src/my_project.cpp
* make some format issues
wq!
pwrforge check
pwrforge fix
pwrforge check
exit
```

## Change pwrforge.toml and update

```console
vi CMakeLists.txt
vi pwrforge.toml
* make some config update
wq!
pwrforge update
vi CMakeLists.txt
q
exit
```

## Debug existing

```console
ls
pwrforge docker run
pwrforge debug
tui enable
b main()
r
n
n
exit
```
