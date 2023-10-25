# 概要
身内でのゲーム会の管理用に作成したdiscord bot。  
遊びたいゲームの候補を/add_candidateコマンドで追加し、/create_pollコマンドで投票フォームを作成する。  
ゲームの候補のテーブルはtext channel/thread毎に管理される。  

# コマンド一覧
## /add_candidate
候補を登録したいtext channel/threadで実行すると、候補登録用のフォームが表示される。  
ゲームの重さは[L|M|H]のいずれか一文字を入力とする。

## /show_candidates
登録済みの候補を表示する。表示はコマンドを実行したユーザにのみ行われる。

## /create_poll
登録済み候補から、投票フォームを作成する。

## /remove_candidate
show_candidateで候補とともに表示されるidを入力すると、大賞の候補が削除される。

## /clear_all_candidates
登録済みのすべての候補が削除される。