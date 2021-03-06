import websockets
import asyncio
import pymongo
import json
from Manager import Manager
from MemberObserver import MemberObserver

class Server:
    def __init__(self):
        self.__port = 8765
        self.__address = "127.0.0.1"
        self.__manager = Manager()
        self.__observers = {}

    async def __signUp(self, data, websocket):
        username = data["username"]
        password = data["password"]

        if self.__manager.isExistedUsername(username):
            await websocket.send(json.dumps({"response": "existedUsername"}))
            return

        self.__manager.createAccount(username, password)
        
        await self.__sendResponseToClient("createdAccount", None, websocket)

    async def __login(self, data, websocket):
        username = data["username"]
        password = data["password"]

        if not self.__manager.validateAccount(username, password):
            await websocket.send(json.dumps({"response": "loginFail"}))
            return
        
        memberObserver = MemberObserver(username, websocket)
        self.__addObserver(memberObserver)
        
        await self.__sendResponseToClient("loginSuccessful", None, websocket)

        boardTitlesAndIds = self.__manager.getUserBoardTitlesAndIds(username)
        
        await self.__sendResponseToClient("userBoardTitlesAndIds", boardTitlesAndIds, websocket)

    async def __sendBoardDetail(self, data, websocket):
        boardId = data["boardId"] 
        detail = self.__manager.getBoardDetail(boardId)
        
        self.__changeObserverCurrentBoardId(websocket, boardId)

        await self.__sendResponseToClient("boardDetail", {
                                             "boardId": boardId,
                                             "boardDetail": detail
                                         }, websocket)

    async def __createBoard(self, data, websocket):
        boardTitle = data["boardTitle"]
        username = data["username"]

        boardId = str(self.__manager.createBoard(boardTitle, username))
        
        await self.__sendResponseToClient("createdBoard", {
                                             'boardTitle': boardTitle,
                                             'boardId': boardId
                                         }, websocket)

    async def __createSection(self, data, websocket):
        boardId = data["boardId"]        
        sectionTitle = data["sectionTitle"]

        sectionId = str(self.__manager.createSection(boardId, sectionTitle))
        
        await self.__sendResponseToClient("createdSection", {
                                             "boardId": boardId,
                                             "sectionTitle": sectionTitle,
                                             "sectionId": sectionId
                                         }, websocket)

    async def __createTask(self, data, websocket):
        boardId = data["boardId"]
        sectionId = data["sectionId"]
        taskTitle = data["taskTitle"]
        taskOrder = data["taskOrder"]

        taskId = str(self.__manager.createTask(sectionId, taskTitle, taskOrder))
        
        await self.__sendResponseToClient("createdTask", {
                                             "boardId": boardId,
                                             "sectionId": sectionId,
                                             "taskId": taskId,
                                             "taskTitle": taskTitle,
                                             "taskOrder": taskOrder
                                         }, websocket)

    async def __editSectionTitle(self, data, websocket):
        sectionId = data["sectionId"]
        sectionTitle = data["sectionTitle"]

        self.__manager.editSectionTitle(sectionId, sectionTitle)

    async def __editTaskTitle(self, data, websocket):
        taskId = data["taskId"]
        taskTitle = data["taskTitle"]

        self.__manager.editTaskTitle(taskId, taskTitle)

    async def __deleteBoard(self, data, websocket):
        boardId = data["boardId"]
        members = self.__manager.getBoardMembers(boardId)
        
        self.__manager.deleteBoard(boardId)
        await self.__updateDeleteBoard(boardId, members, websocket)

    async def __deleteSection(self, data, websocket):
        boardId = data["boardId"]
        sectionId = data["sectionId"]
        
        self.__manager.deleteSection(boardId, sectionId)

    async def __deleteTask(self, data, websocket):
        sectionId = data["sectionId"]
        taskId = data["taskId"]
        
        self.__manager.deleteTask(sectionId, taskId)
        
    async def __deleteTaskComment(self, data, websocket):
        taskId = data["taskId"]
        taskCommentOrder = data["taskCommentOrder"]
        
        self.__manager.deleteTaskComment(taskId, taskCommentOrder)
        
    async def __deleteTaskTag(self, data, websocket):
        taskId = data["taskId"]
        taskTag = data["taskTag"]
        
        self.__manager.deleteTaskTag(taskId, taskTag)

    async def __reorderTaskInSameSection(self, data, websocket):
        sectionId = data["sectionId"]
        taskId = data["taskId"]
        taskOrder = data["taskOrder"]

        self.__manager.reorderTaskInSameSection(sectionId, taskId, taskOrder)

    async def __reorderTaskInDifferentSection(self, data, websocket):
        sectionId = data["sectionId"]
        newSectionId = data["newSectionId"]
        taskId = data["taskId"]
        taskOrder = data["taskOrder"]

        self.__manager.reorderTaskInDifferentSection(sectionId, newSectionId, taskId, taskOrder)

    async def __addTaskComment(self, data, websocket):
        taskId = data["taskId"]
        taskComment = data["taskComment"]
        memberUsername = data["memberUsername"]
        taskCommentOrder = data["taskCommentOrder"]
        
        self.__manager.addTaskComment(taskId, taskComment, memberUsername, taskCommentOrder)

    async def __addTaskTag(self, data, websocket):
        taskId = data["taskId"]
        taskTag = data["taskTag"]
        taskTagColor = data["taskTagColor"]

        self.__manager.addTaskTag(taskId, taskTag, taskTagColor)
        
    async def __addMemberToBoard(self, data, websocket):
        boardId = data["boardId"]
        memberUsername = data["memberUsername"]
        
        if not self.__manager.isExistedUsername(memberUsername):
            await self.__sendResponseToClient("memberUsernameDoesNotExist", None, websocket)
            return
        
        if self.__manager.isMemberInBoard(boardId, memberUsername):
            return
        
        self.__manager.addMemberToBoard(boardId, memberUsername)
        
        boardTitlesAndIds = self.__manager.getUserBoardTitlesAndIds(memberUsername)
        
        await self.__sendResponseToClient("addedMemberToBoard", None, websocket)
        
        if self.__isOnline(memberUsername):
            try:
                memberObserver = self.__observers[memberUsername]
                memberWebsocket = memberObserver.getClientWebsocket()
                
                await self.__sendResponseToClient("updateBoardTitlesAndIds", boardTitlesAndIds, memberWebsocket)
            except:
                return
        
    async def __setTaskResponsibleMember(self, data, websocket):
        taskId = data["taskId"]
        memberUsername = data["memberUsername"]
        
        self.__manager.setTaskResponsibleMember(taskId, memberUsername)

    async def __setTaskDueDate(self, data, websocket):
        taskId = data["taskId"]
        taskDueDate = data["taskDueDate"]

        self.__manager.setTaskDueDate(taskId, taskDueDate)

    async def __setTaskFinishState(self, data, websocket):
        taskId = data["taskId"]
        taskFinishState = data["taskFinishState"]

        self.__manager.setTaskFinishState(taskId, taskFinishState)
        
    async def __updateBoardDetail(self, websocket):
        username = self.__getUsernameFromWebsocket(websocket)
        observer = self.__observers[username]
        currentBoardId = observer.getCurrentBoardId()
        boardDetail = self.__manager.getBoardDetail(currentBoardId)
        members = self.__manager.getBoardMembers(currentBoardId)
        data = {"boardId": currentBoardId, "boardDetail": boardDetail}
        
        members.remove(username)
        
        updateMembers = self.__getOnlineBoardMembersOpeningCurrentBoard(members, currentBoardId)
    
        await self.__notifyObservers(updateMembers, data, "updateBoard")
        
    async def __updateDeleteBoard(self, boardId, members, websocket):
        username = self.__getUsernameFromWebsocket(websocket)
        observer = self.__observers[username]
        data = {"deletedBoardId": boardId}
        
        members.remove(username)
        
        membersOpeningDeletedBoard = self.__getOnlineBoardMembersOpeningCurrentBoard(members, boardId)
        membersNotOpeningDeletedBoard = self.__getOnlineBoardMembersNotOpeningCurrentBoard(members, boardId)
        
        await self.__notifyObservers(membersOpeningDeletedBoard, data, "deletedBoardError")
        await self.__notifyObservers(membersNotOpeningDeletedBoard, data, "deletedBoard")

    async def __notifyObservers(self, members, data, response):
        for member in members:
            memberObserver = self.__observers[member]
            
            await memberObserver.update(data, response)
            
            
    async def __sendResponseToClient(self, response, data, websocket):
        await websocket.send(json.dumps({"response": response, "data": data}))
            
    def __addObserver(self, memberObserver):
        self.__observers[memberObserver.getUsername()] = memberObserver
        
    def __changeObserverCurrentBoardId(self, websocket, boardId):
        username = self.__getUsernameFromWebsocket(websocket)
        observer = self.__observers[username]
        
        observer.changeCurrentBoardId(boardId)
        
    def __getUsernameFromWebsocket(self, websocket):
        for username, observer in self.__observers.items():
            if observer.getClientWebsocket() == websocket:
                return username
    
    def __getOnlineBoardMembersOpeningCurrentBoard(self, members, boardId):
        onlineMembers = self.__getOnlineMembers(members)
        
        return list(filter(lambda member: self.__isOpeningCurrentBoard(member, boardId), onlineMembers))
    
    def __getOnlineBoardMembersNotOpeningCurrentBoard(self, members, boardId):
        onlineMembers = self.__getOnlineMembers(members)
        
        return list(filter(lambda member: not self.__isOpeningCurrentBoard(member, boardId), onlineMembers))
    
    def __getOnlineMembers(self, members):
        return list(filter(lambda member: self.__isOnline(member), members))
    
    def __isOnline(self, username):
        return username in self.__observers
    
    def __isOpeningCurrentBoard(self, member, boardId):
        observer = self.__observers[member]
        
        return observer.getCurrentBoardId() == boardId
   
    async def __handleMessage(self, message, websocket):
        action = message["action"]

        if action == 'signUp':
            await self.__signUp(message["data"], websocket)

        elif action == 'login':
            await self.__login(message["data"], websocket)

        elif action == 'createBoard':
            await self.__createBoard(message["data"], websocket)

        elif action == 'createSection':
            await self.__createSection(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'createTask':
            await self.__createTask(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'requestBoardDetail':
            await self.__sendBoardDetail(message["data"], websocket)

        elif action == 'editSectionTitle':
            await self.__editSectionTitle(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'editTaskTitle':
            await self.__editTaskTitle(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'deleteBoard':
            await self.__deleteBoard(message["data"], websocket)

        elif action == 'deleteSection':
            await self.__deleteSection(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'deleteTask':
            await self.__deleteTask(message["data"], websocket)
            await self.__updateBoardDetail(websocket)
            
        elif action == 'deleteTaskComment':
            await self.__deleteTaskComment(message["data"], websocket)
            await self.__updateBoardDetail(websocket)
            
        elif action == 'deleteTaskTag':
            await self.__deleteTaskTag(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'reorderTaskInSameSection':
            await self.__reorderTaskInSameSection(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'reorderTaskInDifferentSection':
            await self.__reorderTaskInDifferentSection(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'addTaskComment':
            await self.__addTaskComment(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'addTaskTag':
            await self.__addTaskTag(message["data"], websocket)
            await self.__updateBoardDetail(websocket)
            
        elif action == 'addMemberToBoard':
            await self.__addMemberToBoard(message["data"], websocket)
            await self.__updateBoardDetail(websocket)
            
        elif action == 'setTaskResponsibleMember':
            await self.__setTaskResponsibleMember(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'setTaskDueDate':
            await self.__setTaskDueDate(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        elif action == 'setTaskFinishState':
            await self.__setTaskFinishState(message["data"], websocket)
            await self.__updateBoardDetail(websocket)

        else:
            return

    def getPort(self):
        return self.__port

    def getAddress(self):
        return self.__address

    async def handleClient(self, websocket, path):
        async for message in websocket:
            message = json.loads(message)

            await self.__handleMessage(message, websocket)


websocketServer = Server()
start_server = websockets.serve(
    websocketServer.handleClient, websocketServer.getAddress(), websocketServer.getPort())
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()
