# Discord-bot
A discord bot that provides functions of join to create, room distribution and game arrangement with scoring system.

## Features
1. Join to create 
    * Once the member arrives at "Join to create" voice channel, bot moves them into their private channel.
    * Once the member leave their personal channel, the channel is removed. 
2. Waiting room for gaming 
    * The waiting room waits for specific amount of players to start a game.
    * Once the number of players meets the requirement, move them into a private game room. 
        > 1. First come, first served.
        > 2. Once leaves the game room, role will be deleted.
        > 3. Once all players leave the game room, room will be deleted.
    * The text channel **game # uploaded** and **game # result** are created simultaneously. 
        * In **game # uploaded** channel, player uploads their game result sreenshot.
            
            ![game # uploaded](/sample_image/upload.png)
            > **game # uploaded** channel will be deleted in 10 seconds after receiving the image

        * Image is then forwarded to **game # result** channel. Server admin will manually enter the score following bot's instructions.
            ![game # result](/sample_image/result.png)
   
        * There are 3 prefix status of **game # result** channel. The name will be changed after the condition is met.

            > 1. **waited丨game # result** : Players haven't upload image.
            > 2. **unchecked丨game # result** : Admin havn't enter the score.
            > 3. **recorded丨game # result** : Everything done.
                    ![Status](/sample_image/status.png)



        * Accroding to the game score convention table, score will be automatically converted in our database.
            |Game score|Win|Lose|
            |----|----|----|
            | 0 - 100 | +35 | -10 |
            | 100 - 200 | +30 | -10 |
            | 200 - 300 | +30 | -15 |
            | 300 - 400 | +25 | -15 |
            | 400 - 500 | +25 | -20 |
            | 500 - 600  | +20 | -20 |
            | 600 - 700  | +20 | -25 |
            | 700 - 800  | +15 | -25 |
            | 800 - 900  | +15 | -30 |
            | 900 - 1000 | +15 | -30 |
            | 1000 - 1100 | +15 | -30 |
            | 1100 - 1600 | +10 |-30 |
            | 1600 +     | +5 | -35 |



    * In **Score** channel, a sum up message of the recorded game result will be posted. The change of total score is shown as well. 

3. Waiting room for team up
    * The waiting room waits for specific amount of players to team up.
    

    
    