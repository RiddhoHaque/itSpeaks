from flaskext.mysql import MySQL
from flask import Flask, render_template, json, request, redirect, session,jsonify, flash, url_for
from werkzeug import generate_password_hash, check_password_hash
import abc, six
import os
from werkzeug.utils import secure_filename
import subprocess
from os import walk
import math

APP_FOLDER = '/home/riddho/itSpeaksFlask'
UPLOAD_FOLDER = '/home/riddho/itSpeaksFlask/static/uploads'
BOOK_ALLOWED_EXTENSIONS = set(['txt'])
COVER_ALLOWED_EXTENSIONS = set(['ani', 'bmp', 'cal', 'fax', 'gif', 'img', 'jbg', 'jpe', 'jpeg', 'jpg', 'mac', 'pbm', 'pcd', 'pcx', 'pct', 'pgm', 'png', 'ppm', 'psd', 'ras', 'tga', 'tiff', 'wmf'])
PROFILE_PHOTO_ALLOWED_EXTENSIONS = set(['ani', 'bmp', 'cal', 'fax', 'gif', 'img', 'jbg', 'jpe', 'jpeg', 'jpg', 'mac', 'pbm', 'pcd', 'pcx', 'pct', 'pgm', 'png', 'ppm', 'psd', 'ras', 'tga', 'tiff', 'wmf'])
DEFAULT_PROFILE_PHOTO = '/static/Profile_Photos/Default_dp.jpg'
GENRES = 19
GENRE_TITLES = ['Nonfiction', 'Essay' , 'Biography' , 'Autobiography' , 'Speech' , 'Drama' , 'Poetry' , 'Fantasy' , 'Humor', 'Fable', 'Fairy Tales', 'Science Fiction' , 'Shorts' , 'Realistic Fiction' , 'Folklore' , 'Historical Fiction' , 'Horror' , 'Mystery' , 'Mythology']

itSpeaksApp=Flask(__name__, static_url_path='/static')
itSpeaksApp.secret_key = 'Shhh...its secret'

__mysql = MySQL()
itSpeaksApp.config['MYSQL_DATABASE_USER'] = 'root'
itSpeaksApp.config['MYSQL_DATABASE_PASSWORD'] = 'qwe123'
itSpeaksApp.config['MYSQL_DATABASE_DB'] = 'itSpeaks'
itSpeaksApp.config['MYSQL_DATABASE_HOST'] = 'localhost'
itSpeaksApp.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
itSpeaksApp.config['APP_FOLDER'] = APP_FOLDER
__mysql.init_app(itSpeaksApp)

INFINITY = 500
dp=[[-1 for x in range(200)] for y in range(200)]
strA=''
strB=''

def f(ap, bp): #Minimum number of moves for Turning prefix of a to b
	if(bp==len(strB)):
		return 0
	if(ap==len(strA)):
		return INFINITY
	if(dp[ap][bp]!=-1):
		return dp[ap][bp]
	if(strA[ap]==strB[bp]):
		dp[ap][bp]=1+f(ap+1, bp+1)
		return dp[ap][bp]
	res=INFINITY
	resA=1+f(ap+1, bp)
	resB=1+f(ap, bp+1)
	resC=1+f(ap+1, bp+1)
	if resA<res:
		res=resA
	if resB<res:
		res=resB	
	if resC<res:
		res=resC
	dp[ap][bp]=res
	return dp[ap][bp]

def editDistanceSubstring(sA, sB): # Minimum number of moves for turning substring of a to b
	strA=sA
	strB=sB
	dp=[[-1 for x in range(len(sA)+5)] for y in range(len(sB)+5)]	
	mn=INFINITY	
	for i in range(len(sA)):
		if f(i, 0) < mn:
			mn=f(i, 0)
	return mn

class searchItem(object):
	def __init__(self, _id, distance):
		self._id=_id
		self._distance=distance

def getdistance(item):
	return item._distance

def getBooksBySearchEditDistance(text):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_getAllBooks')
	allBooks=cursor.fetchall()
	bookList=[]
	for book in allBooks:
		opt1=editDistanceSubstring(book[1], text)
		opt2=editDistanceSubstring(book[2], text)
		opt3=editDistanceSubstring(book[3], text)		
		mindis=opt1
		if(opt2<mindis):
			mindis=opt2
		if(opt3<mindis):
			mindis=opt3
		if(mindis<5):
			bookList.append(searchItem(book[0], mindis))
	sortedlist=sorted(bookList, key = getDistance)
	idlist=[sortedItem.id for sortedItem in sortedList]
	conn.commit()
	conn.close()
	cursor.close()
	print(idlist)
	return idlist
	
def getUsersBySearchEditDistance(text):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_getAllUsers')
	allUsers=cursor.fetchall()
	userList=[]
	for user in allUsers:
		opt1=editDistanceSubstring(user[1], text)
		opt2=editDistanceSubstring(user[2], text)
		mindis=opt1
		if(opt2<mindis):
			mindis=opt2
		if(mindis<5):
			userList.append(searchItem(user[0], mindis))
	sortedlist=sorted(userList, key = getDistance)
	idlist=[sortedItem.id for sortedItem in sortedList]
	conn.commit()
	conn.close()
	cursor.close()
	print(idlist)
	return idlist

def getInformationForBook(bookID):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_getBookNameAuthor', (bookID, ))	
	bookInfo=cursor.fetchall()
	cursor.callproc('sp_isBookRated', (bookID, ))
	rating_count=cursor.fetchall()	
	ratingMessage='No ratings yet!'
	if int(rating_count[0][0])!=0:
		cursor.callproc('sp_getBookRating', (bookID,))
		rating_data=cursor.fetchall()
		ratingMessage="%.2f/5" % rating_data[0][0]	
	book_dict={
		'bookID' : bookID,		
		'name' : bookInfo[0][0],
		'author' : bookInfo[0][1],
		'thumbnail' : bookInfo[0][2],
		'ratingMessage' : ratingMessage
	}
	conn.commit()	
	conn.close()
	cursor.close()
	return book_dict

def getInformationForUser(userID):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_getNameAndDP', (userID, ))		
	userInfo=cursor.fetchall()	
	conn.commit()	
	conn.close()
	cursor.close()	
	user_dict={
		'username' : userInfo[0][2],
		'name' : userInfo[0][0],
		'profilePhoto' : userInfo[0][1]
	}
	return user_dict


class Unfollowed(object):
	def __init__(self, userID):
		self.userID=userID
		self.weight=0.0
		self.friendOfFriend=False
		self.ratingMatchCount=0
		self.ratingMatchValue=0.0
		self.interestMatch=0
			
	def isFriendOfFriend(self):
		self.friendsOfFriend=True

	def interestMatching(self, match):
		if match>10.0:
			match=10.0
		self.interestMatch=match

	def ratingMatch(self, cosineDistance, _vector_size):
		self.ratingMatchCount=_vector_size
		self.ratingMatchValue=cosineDistance

	def calcWeight(self):
		rem_value=100.0
		if(self.ratingMatchCount>7):
			self.ratingMatchCount=7
		self.weight=self.weight+self.ratingMatchValue*self.ratingMatchCount*5.0
		rem_value=rem_value-self.ratingMatchCount*5.0
		self.weight=self.weight+self.interestMatch*0.7*rem_value
		if self.friendsOfFriend:
			self.weight=self.weight+0.3 


def getWeight(unfollowed):
	return unfollowed.weight		

def parity(num):
	cnt=0
	while num>0:
		if((num & 1)!=0):
			cnt=cnt+1
		num=num>>1
	return cnt

def cosineProduct(A, B):
	normA=0.0
	normB=0.0
	dot=0.0
	lenA=len(A)
	for i in range(lenA):
		dot=dot+A[i]*B[i]
		normA=normA+A[i]*A[i]
		normB=normB+B[i]*B[i]
	normA=math.sqrt(normA)
	normB=math.sqrt(normB)
	return math.cos(dot/(normA*normB))			

def getSuggestedFriendList(userID):		
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_getMaxUserId')
	maxData=cursor.fetchall()
	pos=[-1 for x in range(maxData[0][0]+1)]	
	cursor.callproc('sp_getNotFollowed', (userID, ))
	userList=cursor.fetchall()
	ind=0
	unfollowedList=[]
	for userid in userList:
		unfollowedList.append(Unfollowed(userid[0]))
		pos[userid[0]]=ind
		ind=ind+1
	
	cursor.callproc('sp_getFriendsOfFriends', (userID, ))
	friendsOfFriends=cursor.fetchall()
	for userid in friendsOfFriends:
		unfollowedList[pos[userid[0]]].isFriendOfFriend()
	

	cursor.callproc('sp_getInterestMask', (userID, ))		
	interestData=cursor.fetchall()
	myInterest=interestData[0][0]
	for user in userList:
		cursor.callproc('sp_getInterestMask', (user[0], ))		
		interestData=cursor.fetchall()	
		theirInterest=interestData[0][0]
		unfollowedList[pos[user[0]]].interestMatching(myInterest & theirInterest)
	
	for user in userList:
		cursor.callproc('sp_getMatchingRatingVector', (user[0], userID))
		vectorData=cursor.fetchall()
		if len(vectorData)>0:		
			A=[]
			B=[]
			for data in vectorData:
				A.append(data[0])
				B.append(data[1])
			unfollowedList[pos[user[0]]].ratingMatch(cosineProduct(A, B), len(A))
	
	for i in range(len(unfollowedList)):
		unfollowedList[i].calcWeight
			
	sortedList=sorted(unfollowedList, key = getWeight)
	
	idlist=[sortedItem.userID for sortedItem in sortedList]
	conn.commit()
	conn.close()
	cursor.close()
	print(idlist)
	return idlist

def getRecommendedBookList(userID):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_getAllBookID')
	recommendedList=cursor.fetchall()
	conn.commit()
	conn.close()
	cursor.close()
	return recommendedList	

def checkIfLoggedIn():
	if 'userid' not in session:
		flash('Sorry, you are not logged in')	
		return False
	return True

@itSpeaksApp.route('/signUp',methods=['POST','GET'])
def addUser():		
	_name=request.form['inputName']
	_email=request.form['inputEmail']
	_gender=request.form['gender']
	_age=request.form['inputAge']
	_username=request.form['inputUsername']
	_password=request.form['inputPassword']
	_nature=request.form['nature']
	#_hashed_password=generate_password_hash(_password)	
	_input_mask=int(0);	
	_interest= request.form.getlist("interest")	
	for i in _interest:
		_input_mask=int(_input_mask)+int((1<<int(i)))	
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_validate_username_and_email', (_username, _email))
	exist_check=cursor.fetchall()	
	if(len(exist_check)!=0):		
		conn.commit()
		conn.close()
		cursor.close()
		flash('User Already Exists!')		
		return redirect('/userLogin')		
	else:	
		cursor.callproc('sp_createUser',(_name, _email, _gender, int(_age), _username, _password, int(_input_mask), _nature))		
		cursor.callproc('sp_addDefaultPhoto', (_username, DEFAULT_PROFILE_PHOTO))				
		conn.commit()	
		conn.close()
		cursor.close()
		
		conn= __mysql.connect()	
		cursor = conn.cursor()		
		cursor.callproc('sp_validateUser', (_username, _password))
		data=cursor.fetchall()		
		session['userid']=data[0][0]		
		conn.commit()	
		conn.close()
		cursor.close()
		return redirect('/userhome')
		
@itSpeaksApp.route('/userRegistration')
def registrationPage():	
	return render_template('signUp.html')

@itSpeaksApp.route('/signIn',methods=['POST','GET'])
def validateUser():
	_username=request.form['inputUsername']
	_password=request.form['inputPassword']
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_validateUser', (_username, _password))
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()	
	if len(data) > 0:
		session['userid']=data[0][0]
		return redirect('/userhome')
	else:
		flash('Incorrect credentials!!')
		return redirect('/userLogin')

@itSpeaksApp.route('/userLogin')
def loginUser():
	return render_template('user_login.html')

@itSpeaksApp.route('/userhome')
def homeOfUser():
	if checkIfLoggedIn()==False:
		return redirect('/')
	cur_id=session['userid']	
	conn=__mysql.connect()
	cursor=conn.cursor()
	cursor.callproc('sp_getUserProfilePhotoAndName', (cur_id, ))
	userData=cursor.fetchall()
	myDP=userData[0][0]
	myName=userData[0][1]
	cursor.callproc('sp_getBlogsFromFollowed', (cur_id, ))
	blogData=cursor.fetchall()	
	blogList=[]	
	for blog in blogData:
		print('Looping')
		userin=blog[1]		
		cursor.callproc('sp_getUserProfilePhotoAndName', (userin, ))
		bloggerData=cursor.fetchall()
		cursor.callproc('sp_getNumberOfUpvotes', (blog[0], ))		
		upvoteCount=cursor.fetchall()		
		cursor.callproc('sp_isUpvoted', (cur_id, blog[0]))		
		myUpvote=cursor.fetchall()		
		isUpvoted=False
		if len(myUpvote) > 0:
			isUpvoted=True
		print(isUpvoted)
		with open(APP_FOLDER+blog[2], 'r') as myfile:
			str=myfile.read().replace('\n', '')		
		blog_dict={
			'upvoteCount' : upvoteCount[0][0],
			'bloggerName' : bloggerData[0][1],
			'bloggerPhoto' : bloggerData[0][0],
			'username' : bloggerData[0][2],
			'blogMessage'	: str,	
			'blogID' : blog[0],
			'isUpvoted' : isUpvoted		
		}
		blogList.append(blog_dict)
	conn.commit()
	conn.close()
	cursor.close()
	recommendedList=getRecommendedBookList(cur_id)
	count=0
	bookRecommendations=[]
	for bookid in recommendedList:
		count=count+1
		if count==5:
			break
		bookRecommendations.append(getInformationForBook(bookid))
	
	suggestedFriends=getSuggestedFriendList(cur_id)
	count=0
	friendSuggestions=[]
	for userid in suggestedFriends:
		count=count+1
		if count==5:
			break
		friendSuggestions.append(getInformationForUser(userid))
	print(len(blogList))
	return render_template('home.html', myDP=myDP, myName=myName, blogList=blogList, bookRecommendations=bookRecommendations, friendSuggestions=friendSuggestions)

@itSpeaksApp.route('/addUpvote/<blogID>')
def addUpvote(blogID):
	if checkIfLoggedIn()==False:
		return redirect('/')
	curr_id=session['userid']
	conn=__mysql.connect()
	cursor=conn.cursor()
	print(curr_id)
	print(blogID)
	cursor.callproc('sp_isUpvoted', (curr_id, blogID))
	myUpvote=cursor.fetchall()
	print(myUpvote)
	if(len(myUpvote)>0):
		cursor.callproc('sp_deleteUpvote', (curr_id, blogID))
		conn.commit()
		conn.close()
		cursor.close()			
		return redirect('/userhome')	
	else:	
		cursor.callproc('sp_addUpvote', (curr_id, blogID))
		conn.commit()
		conn.close()
		cursor.close()		
		return redirect('/userhome')	


def allowed_book_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in BOOK_ALLOWED_EXTENSIONS

def allowed_cover_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in COVER_ALLOWED_EXTENSIONS

def allowed_profile_photo_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in PROFILE_PHOTO_ALLOWED_EXTENSIONS

@itSpeaksApp.route('/logout')
def endSession():
	session.pop('userid',None)
	flash('Byebye')	
	return redirect('/')

def get_book_name(uploader_id):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_get_next_book_id')
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	return 'texts/'+str(uploader_id) + '_' + str(data[0][0])+'.txt'

def get_cover_name(uploader_id):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_get_next_book_id')
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	return 'covers/'+str(uploader_id) + '_' + str(data[0][0])+ '.jpg'

def get_folder_name(uploader_id):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_get_next_book_id')
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	return 'audiobooks/'+str(uploader_id) + '_' + str(data[0][0])

def get_ProfilePhoto_name(uploader_id):
	return 'Profile_Photos/'+str(uploader_id)+'.jpg'

def get_blog_name(uploader_id):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_get_next_blog_id')
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	return '/static/uploads/blogs/'+str(uploader_id) + '_' + str(data[0][0])

def get_review_name(uploader_id):
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_get_next_review_id')
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	return 'reviews/'+str(uploader_id) + '_' + str(data[0][0])

def textToWav(text,folder_name, cnt):
   subprocess.call(["espeak", "-w"+folder_name+'/'+str(cnt)+".wav", text, "-s "+str(100)])

@itSpeaksApp.route('/addBook',methods=['POST','GET'])
def addBook():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	return render_template('addBook.html')



@itSpeaksApp.route('/bookAddition',methods=['POST','GET'])
def addToLibrary():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	_title=request.form['bookName']
	_author=request.form['authorName']
	_year=request.form['year']
	_publisher=request.form['publisher']
	_privacy_status=request.form['isPrivate']
	_genre_mask=int(0);	
	_genres= request.form.getlist("genres")	
	_uploader_id= session['userid']	
	for i in _genres:
		_genre_mask=int(_genre_mask)+int((1<<int(i)))			
	if 'book' not in request.files:
		flash('No text to upload')
		return redirect('/addBook')
	book = request.files['book']
	if book.filename == '':
		flash('No selected file')
		return redirect('/addBook')
	if book and allowed_book_file(book.filename):
		_bookfilename = get_book_name(_uploader_id)
		book.save(os.path.join(itSpeaksApp.config['UPLOAD_FOLDER'], _bookfilename))	
	bookCover=request.files.get('bookCover', None)
	if bookCover is None:
		_coverfilename='covers/default_book_cover.jpg'
	else:
		_coverfilename = get_cover_name(_uploader_id)
		bookCover.save(os.path.join(itSpeaksApp.config['UPLOAD_FOLDER'], _coverfilename))
	_foldername=get_folder_name(_uploader_id)	
	_folderpath=UPLOAD_FOLDER+'/'+_foldername
	os.makedirs(_folderpath)
	file = open(UPLOAD_FOLDER+'/'+_bookfilename, "r")
	text=file.read()
	cnt=0
	l=0
	r=min(len(text), 1000)
	while(l<len(text)):
		if(r== len(text)):
			textToWav(text[l:], _folderpath, cnt)			
		else:		
			textToWav(text[l: -(len(text)-r)], _folderpath, cnt)
		cnt=cnt+1
		l=r+1
		r=r+1000
		r=min(r, len(text))
		
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_addBook', (_title, _author, _genre_mask, _year, _publisher, _privacy_status, '/static/uploads'+'/'+_bookfilename, '/static/uploads'+'/'+_coverfilename, '/static/uploads/'+_foldername, _uploader_id))
	data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	flash('book added to library')
	return redirect('/userhome')

@itSpeaksApp.route('/blogAddition', methods=['POST','GET'])
def addBlog():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	_text=request.form['statusBody']
	print(_text)
	_uploader_id= session['userid']
	if not _text:
		flash('Nothing to post')
		return redirect('/userhome')
	file_name=get_blog_name(_uploader_id)
	f= open(APP_FOLDER+file_name,"w+")	
	f.write(_text)
	f.close()
	conn= __mysql.connect()	
	cursor = conn.cursor()
	cursor.callproc('sp_addBlog', (_uploader_id, file_name))
	data=cursor.fetchall()
	conn.commit()
	conn.close()
	cursor.close()
	return redirect('/userhome')

@itSpeaksApp.route('/search', methods=['POST','GET'])
def searchResults():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	_search_text=request.form['searchBar']
	pattern= '%' + _search_text + '%'
	
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_searchBooks', (pattern,))	
	book_data=cursor.fetchall()
	list_of_books=[]
	cnt=0	
	for book in book_data:
		book_dict={
			'bookID' : book[0],
			'name' : book[1],
			'author' : book[2],
			'year' : book[4],
			'publisher' : book[7],
			'thumbnailAddress' : book[8]		
		}
		print (book_dict['thumbnailAddress'])
		list_of_books.append(book_dict)
		cnt=cnt+1
		if cnt==4:
			break	
	conn.commit()
	conn.close()
	cursor.close()

	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_searchUsers', (pattern,))
	user_data=cursor.fetchall()	
	list_of_users=[]
	cnt=0
	for user in user_data:
		user_dict={
			'name' : user[1],
			'gender' : user[3],
			'username' : user[5],
			'about' : user[9],
			'profilePhoto' : user[10]		
		}
		list_of_users.append(user_dict)
		cnt=cnt+1
		if cnt==4:
			break
	conn.commit()
	conn.close()
	cursor.close()

	return render_template('search.html', searchWord=_search_text, bookList=list_of_books, userList=list_of_users)


@itSpeaksApp.route('/searchAllBooks', methods=['POST','GET'])
def searchBookResults():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	_search_text=request.form['searchBar']
	idList=getBooksBySearchEditDistance(text)	
	list_of_books=[]
	for bookid in idList:
		list_of_books.append(getInformationForBook(bookid))
	conn.commit()
	conn.close()
	cursor.close()
	return render_template('searchAllBooks.html', searchWord=_search_text, bookList=list_of_books)

@itSpeaksApp.route('/searchAllUsers', methods=['POST','GET'])
def searchUserResults():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	_search_text=request.form['searchBar']
	idList=getUsersBySearchEditDistance(text)	
	list_of_users=[]
	for userid in idList:
		list_of_users.append(getInformationForUser(userid))
	conn.commit()
	conn.close()
	cursor.close()
	return render_template('searchAllUsers.html', searchWord=_search_text, userList=list_of_users)


@itSpeaksApp.route('/bookProfile/<bookId>')
def getBookProfile(bookId):
	if checkIfLoggedIn()==False:
		return redirect('/')	
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getBookData', (bookId,))	
	book_data=cursor.fetchall()
	
	cursor.callproc('sp_getUploaderName', (bookId,))
	uploaderName=cursor.fetchall()
	
	cursor.callproc('sp_isBookRated', (bookId, ))
	rating_count=cursor.fetchall()	
	ratingMessage='No ratings yet!'
	if int(rating_count[0][0])!=0:
		cursor.callproc('sp_getBookRating', (bookId,))
		rating_data=cursor.fetchall()
		ratingMessage="%.2f/5" % rating_data[0][0]

	cursor.callproc('sp_getBookReviews', (bookId, ))
	reviewList=cursor.fetchall()
	
	cursor.callproc('sp_getNumberOfReads', (bookId, ))
	read_count_data=cursor.fetchall()
	readCount=read_count_data[0]
	
	conn.commit()
	conn.close()
	cursor.close()
	
	genreList=[]
	for i in range(19):
		if((book_data[0][3] & (1<<i))!=0):
			genreList.append(GENRE_TITLES[i])

	book_dict={
		'name': book_data[0][1],
		'author': book_data[0][2],
		'uploaderName' : uploaderName[0][0],
		'year'	: book_data[0][4],
		'publisher' : book_data[0][7],
		'thumbnailAddress' : book_data[0][8],
		'readCount' : readCount[0],
		'rating' : ratingMessage
	}
	
	reviewDicts=[]
	for review in reviewList:
		conn= __mysql.connect()
		cursor = conn.cursor()
		print('Calling')		
		cursor.callproc('sp_getReviewerName', (review[0],))	
		reviewerData=cursor.fetchall()
		print(len(reviewerData))
		print(len(reviewerData[0]))		
		conn.commit()
		conn.close()
		cursor.close()
		print(review)
		with open(APP_FOLDER+review[3], 'r') as myfile:
			str=myfile.read().replace('\n', '')
		print(str)		
		print(len(reviewerData[0]))		
		reviewDict={
			'name' : reviewerData[0][0],
			'profilePhoto' : reviewerData[0][1],
			'reviewBody' : str					
		}
		print('appending')
		reviewDicts.append(reviewDict)
	
	conn= __mysql.connect()
	cursor = conn.cursor()
		
	cursor.callproc('sp_getMyThumbnail', (session['userid'],))	
	myProfilePic=cursor.fetchall()
	conn.commit()
	conn.close()
	cursor.close()

	return render_template('bookProfile.html', book=book_dict, genreList=genreList, revList=reviewDicts, bookID=bookId, myDP=myProfilePic[0][0])	

@itSpeaksApp.route('/bookProfile/rating/<rating>/<bookID>', methods=['POST','GET']) 
def addRating(rating, bookID):
	if checkIfLoggedIn()==False:
		return redirect('/')
	userID=session['userid']
	
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_deleteRating', (userID, bookID))
	conn.commit()
	conn.close()
	cursor.close()
	
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_addRating', (userID,  bookID, rating))
	conn.commit()
	conn.close()
	cursor.close()
	return redirect('/bookProfile/'+str(bookID))


def addRead(userID, bookID):
	if checkIfLoggedIn()==False:
		return redirect('/')
	print(bookID)
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_isBookReadByUser', (userID, bookID) )
	isRead=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	if(len(isRead)==0):
		conn= __mysql.connect()
		cursor = conn.cursor()
		cursor.callproc('sp_addRead', (userID, bookID) )
		conn.commit()
		conn.close()
		cursor.close()

@itSpeaksApp.route('/bookProfile/readBook/<bookID>', methods=['POST','GET'])
def getBookText(bookID):
	if checkIfLoggedIn()==False:
		return redirect('/')	
	addRead(session['userid'], bookID)
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getBookText', (bookID,) )
	book_data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	return render_template('readBook.html', bookName=book_data[0][0], author=book_data[0][1], filename=book_data[0][2])

@itSpeaksApp.route('/bookProfile/playBook/<bookID>', methods=['POST','GET'])
def getBookAudio(bookID):
	if checkIfLoggedIn()==False:
		return redirect('/')
	addRead(session['userid'], bookID)
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getBookAudio', (bookID,) )
	book_data=cursor.fetchall()	
	conn.commit()
	conn.close()
	cursor.close()
	fileList=[]
	audioList=[]
	for (dirpath, dirnames, filenames) in walk(APP_FOLDER+book_data[0][2]):
		fileList.extend(filenames)
		break
	for files in fileList:
		audioList.append(book_data[0][2]+'/'+files)
	audioList.reverse()	
	return render_template('playBook.html', bookName=book_data[0][0], author=book_data[0][1], audioList=audioList)
	

@itSpeaksApp.route('/reviewAddition', methods=['POST','GET'])
def addReview():
	if checkIfLoggedIn()==False:
		return redirect('/')
	userID=session['userid']
	text=request.form['statusBody']
	bookId=request.form['bookID']	
		
	if not text:
		flash('Nothing to post')
		return redirect('/bookProfile/'+str(bookId))

	file_name=UPLOAD_FOLDER+"/"+get_review_name(userID)
	f= open(file_name,"w+")	
	f.write(text)
	f.close()
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_addReview', (userID, bookId,  '/static/uploads'+'/'+get_review_name(userID)))
	conn.commit()	
	conn.close()
	cursor.close()
	flash('Review Added')
	return redirect('/bookProfile/'+str(bookId))


	

@itSpeaksApp.route('/userProfile/<username>')
def showUserProfile(username):
	if checkIfLoggedIn()==False:
		return redirect('/')
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getUserInformation', (username,))
	userInfo=cursor.fetchall()
	sessionUserId=session['userid']
	uploadedBooks=[]	
	readBooks=[]	
	if userInfo[0][0] != sessionUserId:
		showEdit=False		
		cursor.callproc('sp_getPublicBooksUploadedByUser', (userInfo[0][0], ))	
		uploadedBooks=cursor.fetchall()
		cursor.callproc('sp_getPublicBooksReadByUser', (userInfo[0][0], ))	
		readBooks=cursor.fetchall()	
	else:
		showEdit=True
		cursor.callproc('sp_getAllBooksUploadedByUser', (userInfo[0][0], ))	
		uploadedBooks=cursor.fetchall()
		cursor.callproc('sp_getPublicBooksReadByUser', (userInfo[0][0], ))
		readBooks=cursor.fetchall()
	cursor.callproc('sp_getAllBlogPosts', (userInfo[0][0], ));
	blogPosts=cursor.fetchall()
	blogInfo=[]
	for blog in blogPosts:
		cursor.callproc('sp_getNumberOfUpvotes', (blog[0], ))
		upvote_count=cursor.fetchall()		
		with open(APP_FOLDER+blog[2], 'r') as myfile:
			mess=myfile.read().replace('\n', '')
		blog_dict={
			'message' : mess,
			'upvotedBy' : upvote_count[0][0]
		}
		blogInfo.append(blog_dict)
	cursor.callproc('sp_getNumberOfFollowers', (userInfo[0][0], ))
	followerCount=cursor.fetchall()	
	userInformation={
		'name' : userInfo[0][1],
		'email' : userInfo[0][2],
		'gender' : userInfo[0][3],
		'age' : userInfo[0][4],
		'nature' : userInfo[0][6],
		'about' : userInfo[0][7],
		'profilePhoto' : userInfo[0][8], 
		'followedBy' : followerCount[0][0]	
	}
	
	genreList=[]
	for i in range(GENRES):
		if((userInfo[0][5] & (1<<i))!=0):
			genreList.append(GENRE_TITLES[i])
	
	cnt=0
	readBookList=[]
	for book in readBooks:
		
		cursor.callproc('sp_isBookRated', (book[0], ))
		rating_count=cursor.fetchall()	
		ratingMessage='No ratings yet!'
		if int(rating_count[0][0])!=0:
			cursor.callproc('sp_getBookRating', (book[0],))
			rating_data=cursor.fetchall()
			ratingMessage="%.2f/5" % rating_data[0][0]

		book_dict={
			'bookID' : book[0],
			'name' : book[1],
			'author' : book[2],
			'thumbnail' : book[3],
			'ratingMessage' : ratingMessage		
		}
		readBookList.append(book_dict)
		cnt=cnt+1
		if(cnt==5):
			break	
	cnt=0	
	uploadedBookList=[]
	for book in uploadedBooks:
		
		cursor.callproc('sp_isBookRated', (book[0], ))
		rating_count=cursor.fetchall()	
		ratingMessage='No ratings yet!'
		if int(rating_count[0][0])!=0:
			cursor.callproc('sp_getBookRating', (book[0],))
			rating_data=cursor.fetchall()
			ratingMessage="%.2f/5" % rating_data[0][0]

		book_dict={
			'bookID' : book[0],
			'name' : book[1],
			'author' : book[2],
			'thumbnail' : book[3],
			'ratingMessage' : ratingMessage		
		}
		uploadedBookList.append(book_dict)
		cnt=cnt+1
		if(cnt==5):
			break

	cursor.callproc('spIsFollowing', (userInfo[0][0], sessionUserId))
	data=cursor.fetchall()
	isFollowing=False
	if len(data)>0 or userInfo[0][0]==sessionUserId:
		isFollowing=True
	conn.commit()	
	conn.close()
	cursor.close()
	return render_template('profile.html', userInformation=userInformation, genreList=genreList, readBookList=readBookList, uploadedBookList=uploadedBookList, blogList=blogInfo, showEdit=showEdit, isFollowing=isFollowing, userName=username)


@itSpeaksApp.route('/addFollow/<username>')
def addFollow(username):
	if checkIfLoggedIn()==False:
		return redirect('/')
	session_id=session['userid']
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getUserInformation', (username,))
	userInfo=cursor.fetchall()
	userid=userInfo[0][0]
	cursor.callproc('spIsFollowing', (userInfo[0][0], session_id))
	data=cursor.fetchall()
	if len(data)==0 and userInfo[0][0]!=session_id:
		cursor.callproc('spAddFollow', (userInfo[0][0], session_id))	
	conn.commit()
	conn.close()
	cursor.close()
	return redirect('/userProfile/' + username)


@itSpeaksApp.route('/myProfile')
def myProfile():
	if checkIfLoggedIn()==False:
		return redirect('/')
	curr_id=session['userid']
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getUserName', (curr_id,))	
	username=cursor.fetchall()
	conn.commit()	
	conn.close()
	cursor.close()	
	return redirect('/userProfile/'+ username[0][0])

@itSpeaksApp.route('/editProfile',methods=['POST','GET'])
def editRequest():
	if checkIfLoggedIn()==False:
		return redirect('/')	
	curr_id=session['userid']
	conn= __mysql.connect()
	cursor = conn.cursor()
	cursor.callproc('sp_getUserInformationById', (curr_id,))	
	userInfo=cursor.fetchall()
	conn.commit()	
	conn.close()
	cursor.close()
	user_dict={
		'name' : userInfo[0][0],
		'email' : userInfo[0][1],
		'gender' : userInfo[0][2],
		'age' : userInfo[0][3],
		'nature' : userInfo[0][5],
		'about' : userInfo[0][6],
		'profilePhoto' : userInfo[0][7]	
	}
	genreMask=userInfo[0][4]
	interests=[]
	for i in range(GENRES):
		checked_status=False		
		if (genreMask & (1<<i))!=0 :
				checked_status=True
		interest_dict={
			'genre' : GENRE_TITLES[i],
			'isChecked' : checked_status,
			'value' : i
		}
		interests.append(interest_dict)
	return render_template('editProfile.html', userInformation=user_dict, interestList=interests)		

@itSpeaksApp.route('/updateProfile',methods=['POST','GET'])
def updateProfile():	
	if checkIfLoggedIn()==False:
		return redirect('/')
	_name=request.form['inputName']
	print(_name)
	_email=request.form['inputEmail']
	_gender=request.form['gender']
	_age=request.form['inputAge']
	_about=request.form['about']
	print(_about)
	_old_password=request.form['oldPassword']	
	_new_password=request.form['newPassword']
	_nature=request.form['nature']
	_input_mask=int(0);	
	_interest= request.form.getlist("interest")	
	for i in _interest:
		_input_mask=int(_input_mask)+int((1<<int(i)))
	print(_interest)
	
	_profilePhoto = request.files.get('profilePhoto', None)
	
	#print(_profilePhoto.filename)	
	#if 'profilePhoto' not in request.files:
	#	print('File nai')	
	conn= __mysql.connect()
	cursor = conn.cursor()
	curr_id=session['userid']
	cursor.callproc('sp_getActualPassword', (curr_id, ))
	data=cursor.fetchall()
	if(data[0][0]==_old_password):
		#print('Here1')
		cursor.callproc('sp_updateUser', (_name, _email, _gender, _age, _about, _nature, _input_mask, curr_id))
		if len(_new_password)>0:
			cursor.callproc('sp_updateUserPassword', (_new_password, curr_id))
		if _profilePhoto is None:
			#print('Here 1000')			
			unused_var=0
		else:
			#print('Here2')
			if allowed_profile_photo_file(_profilePhoto.filename):			
				_profilePhotoName = get_ProfilePhoto_name(curr_id)
				_profilePhoto.save(APP_FOLDER+'/static/'+_profilePhotoName)
				cursor.callproc('sp_updateProfilePicture', ('/static/'+_profilePhotoName, curr_id))					
		conn.commit()	
		conn.close()
		cursor.close()
		return redirect('/myProfile')	
	
	else:
		flash('Wrong Password!')
		#print('Here3')
		conn.commit()	
		conn.close()
		cursor.close()		
		return redirect('/editProfile')


@itSpeaksApp.route('/')
def main():    
    return render_template('index.html')


if __name__ == "__main__":
    itSpeaksApp.run(host = '0.0.0.0', port=8080)
