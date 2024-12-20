import sys
class ValueExceedsLimitError(Exception): pass

def play_group_link_creator(baselink,high_range,extension="rar"):
  """ receives base link, highest number of link and optional extension 
      Play group formats their links based on how many there are using "0" as padding 
  """

  high_range = int(high_range)+1 #exclusive python range fix
  try:
    if high_range > 1000:
      raise ValueExceedsLimitError("Error: Value exceeds range of 1-999")
  except ValueExceedsLimitError as e: 
    print(e)
    return


  if high_range < 100:
    for i in range(1,high_range):
      if i < 10:
        number = str(i)
        print(f'{baselink}00{number}.{extension}')
      else:
        number = str(i)
        print(f'{baselink}0{number}.{extension}')
  
  
  if high_range > 100:
    for i in range(1,high_range):
      if i < 10:
        number = str(i)
        print(f'{baselink}00{number}.{extension}')
      elif i > 9 and i <100:
        number = str(i)
        print(f'{baselink}0{number}.{extension}')
      else:
        number= str(i)
        print(f'{baselink}{number}.{extension}')

  
  

if __name__ == "__main__": 

  if len(sys.argv) < 3:
      print("Not enough command-line arguments were provided.")    
  elif len(sys.argv) == 3:
    play_group_link_creator(sys.argv[1],sys.argv[2])
  elif len(sys.argv) == 4:
    play_group_link_creator(sys.argv[1],sys.argv[2],sys.argv[3])
  else:
    print("too many command line arguments provided.")
  
 

