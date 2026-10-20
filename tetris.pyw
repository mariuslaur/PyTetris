import sys
import tkinter
import threading
import random
import time

# Default values section

ScreenMaxX = 260 # Canvas size on X axis
ScreenMaxY = 480 # Canvas size on Y axis

# Color settings
DefaultBG = "#AAAAAA" # canvas backgound
AShapeBG  = "#42b0f4" # AShape rectangles color
BShapeBG  = "#f1f441" # BShape rectangles color
CShapeBG  = "#82f441" # CShape rectangles color
DShapeBG  = "#d341f4" # DShape rectangles color
EShapeBG  = "#f4a341" # DShape rectangles color

GridUnit = 20 # Screen grid: square unit [pixels]
ox = 1 # Screen grid: origin on X axis [grid units]
oy = 1 # Screen grid: origin on Y axis [grid units]
mox = int(ScreenMaxX / GridUnit) - 1 # Screen grid: maximum on X axis [grid units]
moy = int(ScreenMaxY / GridUnit) - 1 # Screen grid: maximum on Y axis [grid units]

# Returns the real position in pixels
def GetRealPosition(gridUnits):
    return (gridUnits * GridUnit)

# Returns the position in grid units
def GetGridPosition(realPosition):
    return int(realPosition / GridUnit)

# Speed related settings
MoveDownDelay = 0.25 # seconds
DropDownDelay = 0.02 # seconds

NormalFont = ('freemono', 10)
colorBlack = "#000000"

DEBUG_FLAG = False
def debug_print(msg='', end=None):
    if DEBUG_FLAG:
        if end is not None:
            print(msg, end = end)
        else:
            print(msg)

class Shape:
    def __init__(self, posx, game, color):
        self.width = None  # this will be overridden by each XShape class
        self.height = None # this will be overridden by each XShape class
        
        self.posx = ox + posx   # apply offset GridUnit on X axis
        self.posy = oy          # apply offset GridUnit on Y axis

        self.moveSide = False
        
        self.game = game
        self.delay = game.delay
        self.canvas = game.canvas
        self.lines = game.lines
        self.color = color
        
        self.rectList = [
            self.createRectangle(self.posx, self.posy, self.posx + 1, self.posy + 1),
            self.createRectangle(self.posx, self.posy + 1, self.posx + 1, self.posy + 2)
        ]
        
        self.rotation = 0
        self.rotations = {}
        self.adjustments = {}

        self.alive = True

    def createRectangle(self, x0, y0, x1, y1):
        return self.canvas.create_rectangle(GetRealPosition(x0), GetRealPosition(y0),
                                            GetRealPosition(x1), GetRealPosition(y1),
                                            fill = self.color, width = 1)
 
    def blockedLeft(self):
        if (self.posx == ox):
            return True
        for rect in self.rectList:
            [x, y] = self.canvas.coords(rect)[0:2]
            gridX = GetGridPosition(x)
            gridY = GetGridPosition(y)
            if (gridX == ox or self.lines[gridY-1][gridX-2] != None):
                return True
        return False
        
    def okToMoveLeft(self):
        response = not self.blockedLeft()
        return response # (self.posx > ox)

    def blockedRight(self):
        if (self.posx == mox - self.width):
            return True
        for rect in self.rectList:
            [x, y] = self.canvas.coords(rect)[0:2]
            gridX = GetGridPosition(x)
            gridY = GetGridPosition(y)
            if (gridX == (mox -1) or self.lines[gridY-1][gridX] != None):
                return True
        return False

    def okToMoveRight(self):
        response = not self.blockedRight()
        return response # (self.posx <= mox - self.width - 1)
        
    def isFullLine(self, line):
        return None not in line
    
    def adjustLines(self, fullLines):
        maxY = max(fullLines)

        # remove the rectangles from full lines
        for y in fullLines: 
            for x in range(mox-1):
                if self.lines[y][x] is not None:
                    self.canvas.delete(self.lines[y][x])                    
                    self.lines[y][x] = None

        # move down the rectangles of the lines not full
        deltaY = 1
        for index in range(maxY-1, -1, -1):
            if index not in fullLines:
                for rect in self.lines[index]:
                    if rect is not None:
                        self.canvas.move(rect, 0, deltaY*GridUnit)
                # shift the index of  current not full line with deltaY
                self.lines[index+deltaY] = self.lines[index][:]
            else:
                if (deltaY < len(fullLines)):
                    deltaY += 1
        for y in range(deltaY):
            for x in range(mox-1):
                self.lines[y][x] = None

    def checkLines(self, addedLines):
        fullLines = []
        for y in addedLines:
            if self.isFullLine(self.lines[y]):
                fullLines.append(y)
        if len(fullLines) > 0:
            self.adjustLines(fullLines)
            self.game.score += (len(fullLines)*2 - 1) * 100
            self.game.printScore()
        for x in range(mox-1):
            if self.lines[0][x] != None:
                self.game.gameOver = True
                self.game.printScore(final=True)
                break
        
    def printLines(self):
        debug_print("=============")
        for line in self.lines:
            for r in line:
                if r is None:
                    debug_print("-", end='')
                else:
                    debug_print("O", end='')
            debug_print()
    
    def addToLines(self):
        addedLines = []
        for rect in self.rectList:
            [x, y] = self.canvas.coords(rect)[0:2]
            gridX = GetGridPosition(x)
            gridY = GetGridPosition(y)
            if self.lines[gridY-1][gridX-1] is not None:
                self.canvas.delete(self.lines[gridY-1][gridX-1])
            self.lines[gridY-1][gridX-1] = rect
            if (gridY-1) not in addedLines:
                addedLines.append(gridY-1)
        self.checkLines(addedLines)
        self.printLines()
        self.game.checkAndUpdateSpeed()
        self.alive = False
       
    def blockedDown(self):
        if (self.posy > moy - self.height - 1):
            return True
        for rect in self.rectList:
            [x, y] = self.canvas.coords(rect)[0:2]
            gridX = GetGridPosition(x)
            gridY = GetGridPosition(y)
            if (gridY == (moy - 1) or self.lines[gridY][gridX-1] != None):
                return True
        return False
    
    def okToMoveDown(self):
        response = False
        if self.blockedDown():
            self.addToLines()
        else:
            response = not self.moveSide
        return response #(self.posy <= moy - self.height - 1)

    def okToRotate(self):
        return True

    def rotate(self):
                #if lock.acquire(True):
                #    try:
                if self.okToRotate():
                    for index in range(len(self.rectList)):
                        rect = self.rectList[index]
                        deltax = self.rotations[self.rotation][index][0]
                        deltay = self.rotations[self.rotation][index][1]
                        dx = GetRealPosition(deltax)
                        dy = GetRealPosition(deltay)
                        self.canvas.move(rect, dx, dy)
        
                    self.posx   += self.adjustments[self.rotation][0]
                    self.posy   += self.adjustments[self.rotation][1]
               
                    self.width  = self.adjustments[self.rotation][2]
                    self.height = self.adjustments[self.rotation][3]            

                    self.rotation += 1
                    self.rotation %= 4
                #    finally:                
                #        lock.release()

    # blocking action to move the shape in any direction with deltax and deltay
    def move(self, deltax, deltay):
        dx = GetRealPosition(deltax)
        dy = GetRealPosition(deltay)
        for rect in self.rectList:
            self.canvas.move(rect, dx, dy)
        self.posx += deltax
        self.posy += deltay

    def moveDown(self):
        # delay before next move down
        time.sleep(self.delay)
        if not self.game.gamePaused and self.okToMoveDown():
            self.move(0, 1)

    def moveDownSingleThreaded(self):
        """Moves the piece down instantly without sleeping, relying on .after timing."""
        if not self.game.gamePaused and self.okToMoveDown():
            self.move(0, 1)

    def moveLeft(self):
        self.moveSide = True
        if not self.game.gamePaused and self.okToMoveLeft():
            self.move(-1, 0)
        self.moveSide = False
        
    def moveRight(self):
        self.moveSide = True
        if not self.game.gamePaused and self.okToMoveRight():
            self.move(1, 0)
        self.moveSide = False
            
    # it makes the shape to drop down by changing the move down delay to the less drop delay
    def drop(self):
        if not self.game.gamePaused:
            self.delay = DropDownDelay
            # Cancel the pending slow tick and trigger a fast one immediately
            self.game.force_immediate_tick()


class AShape(Shape):
    def __init__(self, posx, game):
        Shape.__init__(self, posx, game, AShapeBG)
        
        self.width  = 1 # [grid units] this could be calculated from rectList below
        self.height = 4 # [grid units] this could be calculated from rectList below
        
        self.rectList += [   
            self.createRectangle(self.posx, self.posy + 2, self.posx + 1, self.posy + 3),
            self.createRectangle(self.posx, self.posy + 3, self.posx + 1, self.posy + 4)
        ]
                
        # -------------------------------------------------------------------------------
        # Shape: |0 [0] |1              |2 [3] |3              |
        #        |  [1] |  [3][2][1][0] |  [2] |               |
        #        |  [2] |               |  [1] |  [0][1][2][3] |
        #        |  [3] |               |  [0] |               |        
        # -------------------------------------------------------------------------------
        # Rotations template:
        # -------------------------------------------------------------------------------
        # Old state    |    New state   |   Rectangle translations to rotate
        # -------------------------------------------------------------------------------
        # 0      ->    |    1           |   { 0:[2,1],   1:[1,0],   2:[0,-1], 3:[-1,-2] }
        # 1      ->    |    2           |   { 0:[-1,2],  1:[0,1],   2:[1,0],  3:[2,-1]  }
        # 2      ->    |    3           |   { 0:[-2,-1], 1:[-1,0],  2:[0,1],  3:[1,2]   }
        # 3      ->    |    0           |   { 0:[1,-2],  1:[0,-1],  2:[-1,0], 3:[-2,1]  }
        # -------------------------------------------------------------------------------
        self.rotations = {
            0 : { 0:[2,1],   1:[1,0],   2:[0,-1], 3:[-1,-2] },
            1 : { 0:[-1,2],  1:[0,1],   2:[1,0],  3:[2,-1]  },
            2 : { 0:[-2,-1], 1:[-1,0],  2:[0,1],  3:[1,2]   },
            3 : { 0:[1,-2],  1:[0,-1],  2:[-1,0], 3:[-2,1]  }
        }
        self.adjustments = {
            0: [-1,  1, 4, 1],
            1: [2,  -1, 1, 4],
            2: [-2,  2, 4, 1],
            3: [1,  -2, 1, 4]
        }

    def okToRotate(self):
        if (self.rotation == 0 and self.posx > mox - 3) or \
           (self.rotation == 0 and self.posx < ox + 1) or \
           (self.rotation == 2 and self.posx > mox - 2) or \
           (self.rotation == 2 and self.posx < ox + 2) or \
           (self.rotation == 1 and self.posy > moy - 4) or \
           (self.rotation == 3 and self.posy > moy - 4):
            return False
        else:
            return True
        

class BShape(Shape):
    def __init__(self, posx, game):
        Shape.__init__(self, posx, game, BShapeBG)

        self.width  = 2 # [grid units] this could be calculated from rectList below
        self.height = 3 # [grid units] this could be calculated from rectList below
        
        self.rectList += [   
            self.createRectangle(self.posx + 1, self.posy + 1, self.posx + 2, self.posy + 2),
            self.createRectangle(self.posx, self.posy + 2, self.posx + 1, self.posy + 3)
        ]

        # ------------------------------------------------------------------------------
        # Shape: |0 [0]    |1           |2    [3]  |3   [2]    |
        #        |  [1][2] |  [3][1][0] |  [2][1]  | [0][1][3] |
        #        |  [3]    |     [2]    |     [0]  |           |
        # ------------------------------------------------------------------------------
        # Rotations template:
        # ------------------------------------------------------------------------------
        # Old state    |    New state   |   Rectangle translations to rotate
        # ------------------------------------------------------------------------------
        # 0      ->    |    1           |   { 0:[1,1],   1:[0,0],  2:[-1,1],  3[-1,-1] }
        # 1      ->    |    2           |   { 0:[-1,1],  1:[0,0],  2:[-1,-1], 3[1,-1]  }
        # 2      ->    |    3           |   { 0:[-1,-1], 1:[0,0],  2:[1,-1],  3[1,1]   }
        # 3      ->    |    0           |   { 0:[1,-1],  1:[0,0],  2:[1,1],   3[-1,1]  }
        # ------------------------------------------------------------------------------
        self.rotations = {
            0 : { 0:[1,1],   1:[0,0],  2:[-1,1],  3:[-1,-1] },
            1 : { 0:[-1,1],  1:[0,0],  2:[-1,-1], 3:[1,-1]  },
            2 : { 0:[-1,-1], 1:[0,0],  2:[1,-1],  3:[1,1]   },
            3 : { 0:[1,-1],  1:[0,0],  2:[1,1],   3:[-1,1]  }
        }
        self.adjustments = {
            0: [-1,  1,  3, 2],
            1: [0,  -1,  2, 3],
            2: [0,   0,  3, 2],
            3: [1,   0,  2, 3]
        }
        
    def okToRotate(self):
        if (self.rotation == 0 and self.posx > mox - 2) or \
           (self.rotation == 0 and self.posx < ox + 1) or \
           (self.rotation == 2 and self.posx > mox - 3) or \
           (self.rotation == 2 and self.posx < ox) or \
           (self.rotation == 0 and self.posy > moy - 4) or \
           (self.rotation == 1 and self.posy > moy - 4) or \
           (self.rotation == 2 and self.posy > moy - 4) or \
           (self.rotation == 3 and self.posy > moy - 4):
            return False
        else:
            return True


class CShape(Shape):
    def __init__(self, posx, game):
        Shape.__init__(self, posx, game, CShapeBG)

        self.width  = 2 # [grid units] this could be calculated from rectList below
        self.height = 3 # [grid units] this could be calculated from rectList below
        
        self.rectList += [   
            self.createRectangle(self.posx, self.posy + 2, self.posx + 1, self.posy + 3),
            self.createRectangle(self.posx + 1, self.posy + 2, self.posx + 2, self.posy + 3)
        ]

        # ------------------------------------------------------------------------------
        # Shape: |0 [0]    |1           |2 [3][2]  |3       [3] |
        #        |  [1]    |  [2][1][0] |     [1]  |  [0][1][2] |
        #        |  [2][3] |  [3]       |     [0]  |            |
        # ------------------------------------------------------------------------------
        # Rotations template:
        # ------------------------------------------------------------------------------
        # Old state    |    New state   |   Rectangle translations to rotate
        # ------------------------------------------------------------------------------
        # 0      ->    |    1           |   { 0:[1,1],   1:[0,0],  2:[-1,-1], 3:[-2,0] }
        # 1      ->    |    2           |   { 0:[-1,1],  1:[0,0],  2:[1,-1],  3:[0,-2] }
        # 2      ->    |    3           |   { 0:[-1,-1], 1:[0,0],  2:[1,1],   3:[2,0]  }
        # 3      ->    |    0           |   { 0:[1,-1],  1:[0,0],  2:[-1,1],  3:[0,2]  }
        # ------------------------------------------------------------------------------
        self.rotations = {
            0 : { 0:[1,1],   1:[0,0],  2:[-1,-1], 3:[-2,0]  },
            1 : { 0:[-1,1],  1:[0,0],  2:[1,-1],  3:[0,-2]  },
            2 : { 0:[-1,-1], 1:[0,0],  2:[1,1],   3:[2,0]   },
            3 : { 0:[1,-1],  1:[0,0],  2:[-1,1],  3:[0,2]   }
        }
        self.adjustments = {
            0: [-1,  1,  3, 2],
            1: [0,  -1,  2, 3],
            2: [0,   0,  3, 2],
            3: [1,   0,  2, 3]
        }
        
    def okToRotate(self):
        if (self.rotation == 0 and self.posx > mox - 2) or \
           (self.rotation == 0 and self.posx < ox + 1) or \
           (self.rotation == 2 and self.posx > mox - 3) or \
           (self.rotation == 2 and self.posx < ox) or \
           (self.rotation == 0 and self.posy > moy - 4) or \
           (self.rotation == 1 and self.posy > moy - 4) or \
           (self.rotation == 2 and self.posy > moy - 4) or \
           (self.rotation == 3 and self.posy > moy - 4):
            return False
        else:
            return True


class DShape(Shape):
    def __init__(self, posx, game):
        Shape.__init__(self, posx, game, DShapeBG)

        self.width  = 2 # [grid units] this could be calculated from rectList below
        self.height = 2 # [grid units] this could be calculated from rectList below
        
        # ------------------------------------------------------------------------------
        # Shape: | [][] |
        #        | [][] |
        # ------------------------------------------------------------------------------
        # No rotation possible.
        # ------------------------------------------------------------------------------
        self.rectList += [   
            self.createRectangle(self.posx + 1, self.posy, self.posx + 2, self.posy + 1),
            self.createRectangle(self.posx + 1, self.posy + 1, self.posx + 2, self.posy + 2)
        ]
        
    def rotate(self):
        return


class EShape(Shape):
    def __init__(self, posx, game):
        Shape.__init__(self, posx, game, EShapeBG)

        self.width  = 2 # [grid units] this could be calculated from rectList below
        self.height = 3 # [grid units] this could be calculated from rectList below
        
        self.rectList += [   
            self.createRectangle(self.posx + 1, self.posy + 1, self.posx + 2, self.posy + 2),
            self.createRectangle(self.posx + 1, self.posy + 2, self.posx + 2, self.posy + 3)
        ]

        # ------------------------------------------------------------------------------
        # Shape: |0 [0]    |1           |2 [3]     |3   [2][3] |
        #        |  [1][2] |     [1][0] |  [2][1]  | [0][1]    |
        #        |     [3] |  [3][2]    |     [0]  |           |
        # ------------------------------------------------------------------------------
        # Rotations template:
        # ------------------------------------------------------------------------------
        # Old state    |    New state   |   Rectangle translations to rotate
        # ------------------------------------------------------------------------------
        # 0      ->    |    1           |   { 0:[1,1],   1:[0,0],  2:[-1,1],  3:[-2,0] }
        # 1      ->    |    2           |   { 0:[-1,1],  1:[0,0],  2:[-1,-1], 3:[0,-2] }
        # 2      ->    |    3           |   { 0:[-1,-1], 1:[0,0],  2:[1,-1],  3:[2,0]  }
        # 3      ->    |    0           |   { 0:[1,-1],  1:[0,0],  2:[1,1],   3:[0,2]  }
        # ------------------------------------------------------------------------------
        self.rotations = {
            0 : { 0:[1,1],   1:[0,0],  2:[-1,1],  3:[-2,0] },
            1 : { 0:[-1,1],  1:[0,0],  2:[-1,-1], 3:[0,-2] },
            2 : { 0:[-1,-1], 1:[0,0],  2:[1,-1],  3:[2,0]  },
            3 : { 0:[1,-1],  1:[0,0],  2:[1,1],   3:[0,2]  }
        }
        self.adjustments = {
            0: [-1,  1,  3, 2],
            1: [0,  -1,  2, 3],
            2: [0,   0,  3, 2],
            3: [1,   0,  2, 3]
        }
        
    def okToRotate(self):
        if (self.rotation == 0 and self.posx > mox - 2) or \
           (self.rotation == 0 and self.posx < ox + 1) or \
           (self.rotation == 2 and self.posx > mox - 3) or \
           (self.rotation == 2 and self.posx < ox) or \
           (self.rotation == 0 and self.posy > moy - 4) or \
           (self.rotation == 1 and self.posy > moy - 4) or \
           (self.rotation == 2 and self.posy > moy - 4) or \
           (self.rotation == 3 and self.posy > moy - 4):
            return False
        else:
            return True


ShapeIds = {
    0: AShape,
    1: BShape,
    2: CShape,
    3: DShape,
    4: EShape
}

ShapeWidths = {
    0: 1,
    1: 2,
    2: 2,
    3: 2,
    4: 2
}


class Game:
    def __init__(self, master, canvas):
        self.master = master
        self.canvas = canvas
        self.lines = self.createLines()
        self.gameOver = False
        self.gamePaused = False
        self.delay = MoveDownDelay
        self.speed = 1
        self.speedText = self.canvas.create_text(ScreenMaxX-65, 3, anchor=tkinter.NW, text="SPEED:")
        self.score = 0
        self.scoreText = self.canvas.create_text(4, 3, anchor=tkinter.NW, text="SCORE:")
        self.loop_job = None  # Tracks the scheduled .after job
        
    def createLines(self):
        lines = []
        # there will be moy-2 active lines
        # a line has mox-2 active GridUnits
        for y in range(moy-1):
            line = []
            for x in range(mox-1):
                line.append(None) # corresponds to: [1...mox-1] used columns
            lines.append(line)    # corresponds to: [1...moy-1] used lines
        return lines

    def createRandShape(self):
        randomShapeId = random.randint(0, len(ShapeIds)-1)
        randPosX = random.randint(0, mox - ShapeWidths[randomShapeId] - 1)
        if hasattr(self, 'shape'):
            del self.shape
        self.shape = ShapeIds[randomShapeId](randPosX, self)
    
    def shapeAlive(self):
        return (self.shape.alive)

    def printSpeed(self):
        self.canvas.delete(self.speedText)
        self.speedText = self.canvas.create_text(ScreenMaxX-65, 3, anchor=tkinter.NW, fill=colorBlack, font=NormalFont, text="SPEED: {}".format(self.speed))

    def printScore(self, final=False):
        if final:
            # create button, link it to clickExitButton()
            self.restartButton = tkinter.Button(self.master, text="Restart game", command=self.restartGame)
            # place button at (0,0)
            self.restartButton.place(x=5, y=ScreenMaxY-27)
            
            # --- FIX: Flash the game over text safely without blocking the main UI loop ---
            def flash_game_over():
                inc = 1
                fontDim = 11
                while self.gameOver and self.canvas.winfo_exists():
                    try:
                        fontDim = fontDim + inc * 2
                        variableFont = ('freemono', fontDim, 'bold')
                        
                        # Use master.after to safely update the text size across threads
                        def update_text(f=variableFont):
                            if self.canvas.winfo_exists():
                                self.canvas.delete(self.scoreText)
                                self.scoreText = self.canvas.create_text(
                                    4, 3, anchor=tkinter.NW, fill=colorBlack, font=f, text="SCORE: {}".format(self.score)
                                )
                        
                        self.master.after(0, update_text)
                        time.sleep(MoveDownDelay)
                        inc = -inc
                    except (tkinter.TclError, RuntimeError):
                        break  # Stop thread if window is destroyed

            # Keep the flashing animation on a throwaway background thread so mainloop never freezes
            threading.Thread(target=flash_game_over, daemon=True).start()
            return

        # Normal score print behavior
        if self.canvas.winfo_exists():
            self.canvas.delete(self.scoreText)
            self.scoreText = self.canvas.create_text(4, 3, anchor=tkinter.NW, fill=colorBlack, font=NormalFont, text="SCORE: {}".format(self.score))
    
    def checkAndUpdateSpeed(self):
        if self.score < 100000:
            self.speed = int(self.score/1000) + 1
            self.delay = MoveDownDelay*(10 - self.speed + 1)/10.0
            self.printSpeed()

    def restartGame(self):
        # 1. Clean up UI elements
        self.restartButton.destroy()
        
        # 2. Reset game state flags and scores
        self.gameOver = False
        self.gamePaused = False
        self.speed = 1
        self.score = 0
        self.delay = MoveDownDelay # Reset fall delay back to level 1 normal speed
        
        # 3. Clear all visual canvas blocks and grid memories
        for line in self.lines:
            for x in range(mox-1):
                r = line[x]
                if r is not None:
                    self.canvas.delete(r)
                line[x] = None
        
        # 4. Redraw score texts to normal sizes
        self.printScore()
        self.printSpeed()
        
        # 5. Generate a clean initial piece and kickstart the core engine ticker again
        self.createRandShape()
        self.game_tick()
        
    def run(self):
        """Sets up keybinds and kicks off the initial loop tick."""
        debug_print("run")
        
        def onArrowLeftKey(event = None):
            if not self.gameOver and not self.gamePaused: self.shape.moveLeft()
        def onArrowRightKey(event = None):
            if not self.gameOver and not self.gamePaused: self.shape.moveRight()
        def onArrowUpKey(event = None):
            if not self.gameOver and not self.gamePaused: self.shape.rotate()
        def onArrowDownKey(event = None):
            if not self.gameOver and not self.gamePaused: self.shape.drop()
        def onPKey(event = None):
            self.gamePaused = not self.gamePaused

        self.canvas.bind_all("<Left>", onArrowLeftKey)
        self.canvas.bind_all("<Right>", onArrowRightKey)
        self.canvas.bind_all("<Up>", onArrowUpKey)
        self.canvas.bind_all("<Down>", onArrowDownKey)
        self.canvas.bind_all("<p>", onPKey)
        
        self.printScore()
        self.printSpeed()
        self.createRandShape()
        
        # Start the non-blocking loop
        self.game_tick()

    def force_immediate_tick(self):
        """Cancels the active scheduled tick and fires a new one instantly."""
        if self.loop_job:
            self.master.after_cancel(self.loop_job)
            self.loop_job = None
        
        # Run the game logic right now
        self.game_tick()

    def game_tick(self):
        """The single-threaded tick handler (Fully updated for clean resets)."""
        if not self.canvas.winfo_exists():
            return

        if not self.gameOver:
            if not self.gamePaused:
                if self.shapeAlive():
                    self.shape.moveDownSingleThreaded()
                else:
                    # Piece just died/landed! Re-calculate normal speed before creating the next piece
                    self.checkAndUpdateSpeed()
                    if not self.gameOver:
                        self.createRandShape()

            # Convert current delay into milliseconds
            delay_ms = int(self.delay * 1000)
            
            # Schedule the next frame
            self.loop_job = self.master.after(delay_ms, self.game_tick)


# --- REFACTORED MAIN ENTRYPOINT (NO THREADING IMPORT REQUIRED) ---
def main():
    master = tkinter.Tk()
    master.title("T E T R I S by π/R")
    master.resizable(width=False, height=False)
    master.minsize(ScreenMaxX+5, ScreenMaxY+20)
    master.maxsize(ScreenMaxX+5, ScreenMaxY+20)

    canvas = tkinter.Canvas(master, bg=DefaultBG, width=ScreenMaxX, height=ScreenMaxY)
    canvas.pack(expand=False)
    canvas.create_rectangle(3, 3, ScreenMaxX, ScreenMaxY, width = 2)
    canvas.create_rectangle(20, 20, ScreenMaxX-20, ScreenMaxY-20, width = 1)
    canvas.focus()
    
    game = Game(master, canvas)

    def on_closing():
        game.gameOver = True
        if game.loop_job:
            master.after_cancel(game.loop_job) # Safely un-schedule pending loops
        debug_print("master destroy")
        master.quit()
        master.destroy()

    master.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Fire up the engine directly on the main event thread
    game.run() 
    master.mainloop()

if __name__ == "__main__":
    main()
