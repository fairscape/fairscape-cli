mkdir y
cd y
fairscape-cli rocrate init \
        --name somenamehahahah \
        --organization-name orgnameasdfasdfasdf \
        --keywords random \
        --keywords "test" \
        --description "my random stuff" \
        --project-name projectnamehahah

fairscape-cli rocrate register computation \
        --name 'name' \
        --run-by 'runby' \
        --date-created '08-03-2023' \
        --command cmd \
        --description "my test computation" \
        --keywords random \
        --keywords "test" \
        --guid e3fa80d6-80b0-44cf-a6d7-6397cc3ef6bf \
        --used-software 'ark:/s1' \
        --used-dataset asdf \
        --generated 'ark:/g1' \
        `pwd`
