#!/bin/bash
# Paco Li, 20150910
# archive and purge utility
# Ode to the Teacher's Day
# Absolutely without warranty, free to copy, use and modify

purge()
{
    SRC_DIR=$1
    RETENTION_DAY=$2
    
    find ${SRC_DIR} -type f -mtime +${RETENTION_DAY} -exec rm -f {} \;
}

purge_ex()
{
    SRC_DIR=$1
    PATTERN=$2
    RETENTION_MIN=$3

    find ${SRC_DIR} -type f -name "${PATTERN}" -mmin +${RETENTION_MIN} -exec rm -f {} \;
}

backup() 
{
    SRC_DIR=$1
    DST_DIR=$2
    BACKUP_DAY=$3

    find ${SRC_DIR} -type f -mtime +${BACKUP_DAY} -exec mv {} ${DST_DIR} \;
}

backup_ex()
{
    SRC_DIR=$1
    DST_DIR=$2
    FILE_PATTERN=$3
    BACKUP_MINUTE=$4

    find ${SRC_DIR} -type f -name "${FILE_PATTERN}" -mmin +${BACKUP_MINUTE} -exec mv {} ${DST_DIR} \;
}

backup_with_timestamp()
{
    SRC_DIR=$1
    DST_DIR=$2
    FILE_PATTERN=$3
    BACKUP_MINUTE=$4

    cd ${SRC_DIR} #change dir so that we get the './basename' of file in {}, facilitate add timestamp
    find -type f -name "${FILE_PATTERN}" -mmin +${BACKUP_MINUTE} -exec mv {} ${DST_DIR}/{}.`date  +%Y%m%d%H%M%S` \;
}

compress()
{
    find $1  -type f ! -name "*.gz" -exec gzip -f {} \;
}

show_usage()
{
    echo "This is a utility to do housekeeping on files, via fulfilling 3 atomic operations: backup, compress and purge"
    echo 
    echo "Usage0: housekeep.sh purge <src_dir> <retention_day>"
    echo "        simply purge files under src_dir which was modifed retention_day earlier"
    echo "Usage1: housekeep.sh purge <src_dir> <file_pattern> <retention_minute>"
    echo "        purge files under src_dir which matches the pattern and was modified time retention_minute earlier"
    echo "Usage2: housekeep.sh backup <src_dir> <dest_dir> <keep_day>"
    echo "        simply archieve via day number"
    echo "Usage3: housekeep.sh backup <src_dir> <dest_dir> <file_pattern> <keep_minute>"
    echo "        archieve via pattern match and the duration is controlled in minute"
    echo "Usage4: housekeep.sh backup <src_dir> <dest_dir> <file_pattern> <keep_minute> ts"
    echo "        The same as Usage3, but the archived filename will be add with a '.YYYYMMDDHHMISS' timestamp"
    echo "Usage5: housekeep.sh gzip <dir>"
    echo "        gzip all not *.gz file under <dir>"
    echo
    echo "Limitation: Dirs should always be full absolute path in Usage4 !!"
    exit
}

if [[ $1 = "backup" ]]; then
    if [ $# = 4 ]; then
        backup $2 $3 $4
    elif [ $# = 5 ]; then
        backup_ex $2 $3 $4 $5
    elif [ $# = 6 ]; then
        backup_with_timestamp $2 $3 $4 $5
    else
        show_usage
    fi
elif [[ $1 = "purge" ]]; then
    if [ $# = 3 ]; then
        purge $2 $3
    elif [ $# = 4 ]; then
        purge_ex $2 $3 $4
    else
        show_usage
    fi
elif [[ $1 = "gzip" ]]; then
    if [ $# = 2 ]; then
        compress $2
    else
        show_usage
    fi
else
    show_usage
fi

## Example:
## using it in crontab:
## #purge files under backup dir older than 90 days
## 5 3 * * * /radius/bin/housekeep.sh purge /radius/backup 90
## #backup log files with ".history" 1440 min(1 day) before, add timestamp to backup file
## 10 3 * * * /radius/bin/housekeep.sh backup "/radius/log/" "/radius/backup/log" "*.history" 1440 ts
## #backup log files under log path 3 days before
## 15 3 * * * /radius/bin/housekeep.sh backup "/radius/log/" "/radius/backup/log" 3 
## #Keep cdr file for 7 days then backup
## 20 3 * * * /radius/bin/housekeep.sh backup "/radius/cdr/" "/radius/backup/cdr/access" "AUTH*" 10080
## 30 3 * * * /radius/bin/housekeep.sh backup "/radius/cdr/" "/radius/backup/cdr/account" "ACCT*" 10080
## 40 3 * * * /radius/bin/housekeep.sh backup "/radius/cdr/" "/radius/backup/cdr/disconn" "DISC*" 10080
## #compress files under backup dir
## 50 3 * * * /radius/bin/housekeep.sh gzip "/radius/backup"
