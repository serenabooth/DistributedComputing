// random notes
// groups have a 'last message timestamp' that's used for sorting upon query.
// everytime a message is sent, need to update that field for the group with the
// new timestamp.

// db tables
Messages = new Meteor.Collection("messages");
Groups = new Meteor.Collection("groups");

// types of message recipients
var recepientTypes = {
		GROUP: 1
};

// REMOVE AFTER TESTING 
// empty accounts and create 3 dummy users
function resetAccounts() {
	// drop table
	Meteor.users.remove({});

	// create new users
	for (var i = 0; i < 4; i++) {
		Accounts.createUser({
			username: "testuser" + (i + 1).toString(),
			password: "testpassword" + (i + 1).toString()
		});
	}
}

// REMOVE AFTER TESTING
// send 3 "group" messages from testuser2 to testuser1
// send 3 "group" messages from testuser2 to testuser1 and testuser3
// send 3 "group" messages from testuser1 to testuser 2, 3, and 4
function sendTestGroupMessages() {
	console.log("called sendTestGroupMessages()");

	// drop tables
	Groups.remove({});
	Messages.remove({});

	// test accounts
	var testuser1 = Meteor.users.findOne({username: "testuser1"});
	var testuser2 = Meteor.users.findOne({username: "testuser2"});
	var testuser3 = Meteor.users.findOne({username: "testuser3"});
	var testuser4 = Meteor.users.findOne({username: "testuser4"});

	// get a new group id number
	var newGroupId = Random.id();

	// insert messages
	// send 3 "group" messages from testuser2 to testuser1
	var curr_date = null;
	for (var i = 0; i < 3; i++) {
		var d = new Date();
		curr_date = (curr_date == null) ? d : curr_date;
		Messages.insert({
			recipientId: newGroupId,
			recipientType: recepientTypes.GROUP,
			id: Random.id(), 
			senderId: testuser2._id,
			createdAt: d,
			content: "Message " + (i + 1).toString() + " from testuser2 to testuser1"
		});
	}

	// insert new group with corresponding groupId
	Groups.insert({
		groupId: newGroupId,
		accountIds: [testuser1._id, testuser2._id],
		mostRecentMessageTimestamp: curr_date
	});

	// get a new group id number
	newGroupId = Random.id();

	// insert messages
	// send 3 "group" messages from testuser2 to testuser1 and testuser3
	curr_date = null;
	for (var i = 0; i < 3; i++) {
		var d = new Date();
		curr_date = (curr_date == null) ? d : curr_date;
		Messages.insert({
			recipientId: newGroupId,
			recipientType: recepientTypes.GROUP,
			messageId: Random.id(), 
			senderId: testuser2._id,
			createdAt: d,
			content: "Message " + (i + 1).toString() + " from testuser2 to testuser1 and testuser3"
		});
	}

	// insert new group with corresponding groupId
	Groups.insert({
		groupId: newGroupId,
		accountIds: [testuser1._id, testuser2._id, testuser3._id],
		mostRecentMessageTimestamp: curr_date
	});

	// get a new group id number
	newGroupId = Random.id();

	// insert messages
	// send 3 "group" messages from testuser1 to testuser 2, 3, and 4
	curr_date = null;
	for (var i = 0; i < 3; i++) {
		var d = new Date();
		curr_date = (curr_date == null) ? d : curr_date;
		Messages.insert({
			recipientId: newGroupId,
			recipientType: recepientTypes.GROUP,
			messageId: Random.id(), 
			senderId: testuser1._id,
			createdAt: d,
			content: "Message " + (i + 1).toString() + " from testuser1 to testuser2, testuser3, testuser4"
		});
	}

	// insert new group with corresponding groupId
	Groups.insert({
		groupId: newGroupId,
		accountIds: [testuser1._id, testuser2._id, testuser3._id, testuser4._id],
		mostRecentMessageTimestamp: curr_date
	});
}

// returns an array of group objects the user is in
function getGroupsUserIsIn() {
	groupsUserIsIn = Groups.find({}, {sort: {mostRecentMessageTimestamp: -1}}).fetch();
	groupsUserIsIn = groupsUserIsIn.filter(function(d) {
		return d.accountIds.indexOf(Meteor.userId()) != -1;
	})
	return groupsUserIsIn;
}

// creates a group name just like facebook messenger
function createGroupNameFromGroupObj(obj) {
	var groupName = "";
	obj.accountIds.forEach(function(id) {
		if (id != Meteor.userId()) {
			if (groupName == "") {
				groupName = Meteor.users.findOne({_id: id}).username;
			}
			else {
				groupName += ", " + Meteor.users.findOne({_id: id}).username;
			}
		}	
	});
	return groupName;
}

// server
if (Meteor.isServer) {
	// testing init
	// resetAccounts();
	sendTestGroupMessages();
}

// client
if (Meteor.isClient) {
	// show no messages on load
	Session.setDefault("groupName", null);
	Session.setDefault("groupNameId", null);

	// set document title
	document.title = "Protocol Buffer Chat";

	// account stuff
	Accounts.ui.config({
    	passwordSignupFields: 'USERNAME_ONLY'
  	});

	// body event handlers
	Template.body.events({
		"click .logCurrentUser": function(event) {
      		event.preventDefault();	// don't submit
			console.log("Here is a log of the current user: ");
			console.log(Meteor.user());
		},
		"click .logUserGroups": function(event) {
			event.preventDefault(); // don't submit
			groupsUserIsIn = Groups.find({}).fetch();
			groupsUserIsIn = groupsUserIsIn.filter(function(d) {
				return d.accountIds.indexOf(Meteor.userId()) != -1;
			});
			console.log("Here is a log of the groups the current user is in: ");
			console.log(groupsUserIsIn);
		}
    });

    // fills in groups on left side
     Template.body.helpers({
    	groups: function() {
			var groupsUserIsIn = getGroupsUserIsIn();
    		var groupNames = [];
    		groupsUserIsIn.forEach(function(group) {
    			groupNames.push(createGroupNameFromGroupObj(group));
    		});
    		returnVal = []
    		groupNames.forEach(function(d) {
    			var obj = {groupName: d};
    			returnVal.push(obj);
    		});
    		return returnVal;
    	}
    });

     // for clicking on a group
     Template.group.events({
     	"click li": function(event) {
     		Session.set("groupName", event.target.innerText);
     		var groupsUserIsIn = getGroupsUserIsIn();
     		groupsUserIsIn.forEach(function(g) {
				if (createGroupNameFromGroupObj(g) == Session.get("groupName")) {
 					Session.set("groupNameId", g.groupId);
 				}     			
     		});	
     	}
     });

     // messages
     Template.messages.helpers({
     	groupChat: function() {
     		return Session.get("groupName");
     	},
     	messages: function() {
     		// TODO: this is stupid and needs to be fixed, but I can't think
     		// of a better way right now. generates all the names of all groups
     		// and whichever names matches Session.get("groupName"), takes the
     		// id of that group and fetches messages
     		var data = Messages.find({recipientId: Session.get("groupNameId")}).fetch();
     		data.forEach(function(d) {
     			d.sender = Meteor.users.findOne({_id: d.senderId}).username;
     		});
     		return data;
		}
     });
}