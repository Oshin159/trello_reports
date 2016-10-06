API_KEY=awk '{if($1=="API_KEY") print $2}' config.txt
API_TOKEN=awk '{if($1=="API_TOKEN") print $2}' config.txt
trelloIndex=$(curl -XGET $1"/_cat/indices?"| awk '/trello-*/{print $3}')
curl -XPOST $1"/"$trelloIndex"/_close"
python $2 $1
